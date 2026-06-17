"""POST /v1/chat/completions — OpenAI-compatible chat proxy.

Resolves the requested model to its upstream llama.cpp server and forwards the
request, supporting both buffered JSON responses and streamed SSE. The model id
is stashed on ``request.state`` so the logging middleware can record it.

Token usage is captured for the dashboard:

* **Non-streaming** — the upstream response carries a ``usage`` block; we stash
  it on ``request.state`` and the logging middleware persists it.
* **Streaming** — we opt into ``stream_options.include_usage`` and sniff the
  trailing usage frame out of the SSE bytes. Because the middleware finishes
  before the body streams, the streaming path owns its own log row (written when
  the generator drains) and sets ``request.state.skip_request_log`` so the
  middleware does not double-log.
"""

from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.deps import ApiKeyDep, DbSession
from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.schemas.openai import ChatCompletionRequest
from app.services.http_client import get_http_client
from app.services.llamacpp import LlamaCppConnector, UpstreamError
from app.services.log_service import LogService
from app.services.model_registry import ModelRegistry

logger = get_logger(__name__)
router = APIRouter()

_ENDPOINT = "/v1/chat/completions"


def _error_response(status_code: int, message: str, err_type: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": err_type, "code": status_code}},
    )


@router.post("/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
    db: DbSession,
    _: ApiKeyDep,
):
    # Record the model on request.state for the logging middleware.
    request.state.model_used = body.model

    model = await ModelRegistry(db).resolve_enabled(body.model)
    if model is None:
        return _error_response(
            404,
            f"The model '{body.model}' does not exist or is not enabled.",
            "model_not_found",
        )

    connector = LlamaCppConnector(get_http_client())
    payload = body.upstream_payload()

    if body.stream:
        # The streaming path logs its own row once the stream drains.
        request.state.skip_request_log = True
        return await _stream(connector, model.endpoint_url, payload, body.model)

    try:
        result = await connector.chat_completion(model.endpoint_url, payload)
    except UpstreamError as exc:
        logger.warning("Upstream error for model %s: %s", body.model, exc.message)
        return JSONResponse(status_code=exc.status_code, content=exc.as_openai_error())

    # Stash usage so the middleware can persist token counts.
    _stash_usage(request, result.get("usage"))
    return JSONResponse(content=result)


async def _stream(
    connector: LlamaCppConnector,
    endpoint_url: str,
    payload: dict[str, Any],
    model_name: str,
) -> StreamingResponse | JSONResponse:
    """Build a StreamingResponse that forwards upstream SSE chunks.

    We begin iterating *before* constructing the response so that connection
    failures surface as a normal JSON error rather than a half-open stream. The
    generator sniffs the usage frame and records the request log when it drains
    (so end-to-end latency and token counts are accurate).
    """
    start = time.perf_counter()
    # Ask the upstream to emit a final usage frame (ignored by servers that
    # don't support it; we simply record null tokens in that case).
    payload = {**payload, "stream_options": {"include_usage": True}}

    agen = connector.chat_completion_stream(endpoint_url, payload)
    try:
        first_chunk = await agen.__anext__()
    except StopAsyncIteration:
        first_chunk = b""
    except UpstreamError as exc:
        logger.warning("Upstream stream error: %s", exc.message)
        await _record_stream_log(
            model_name, exc.status_code, (time.perf_counter() - start) * 1000, None
        )
        return JSONResponse(status_code=exc.status_code, content=exc.as_openai_error())

    captured: dict[str, Any] = {"usage": None}

    async def event_stream():
        try:
            if first_chunk:
                _sniff_usage(first_chunk, captured)
                yield first_chunk
            async for chunk in agen:
                _sniff_usage(chunk, captured)
                yield chunk
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            await _record_stream_log(model_name, 200, latency_ms, captured["usage"])

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _stash_usage(request: Request, usage: Any) -> None:
    """Copy an OpenAI ``usage`` dict onto request.state for the middleware."""
    usage = usage or {}
    request.state.prompt_tokens = usage.get("prompt_tokens")
    request.state.completion_tokens = usage.get("completion_tokens")
    request.state.total_tokens = usage.get("total_tokens")


def _sniff_usage(chunk: bytes, captured: dict[str, Any]) -> None:
    """Capture the trailing usage-only SSE frame from a chunk, if present."""
    for line in chunk.split(b"\n"):
        if not line.startswith(b"data: "):
            continue
        payload = line[6:].strip()
        if not payload or payload == b"[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except (ValueError, TypeError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get("usage"), dict):
            captured["usage"] = obj["usage"]


async def _record_stream_log(
    model_name: str, status_code: int, latency_ms: float, usage: Any
) -> None:
    """Write the request-log row for a streamed completion.

    Uses its own DB session because the request-scoped session is closed by the
    time the stream drains. Logging failures never break the response.
    """
    usage = usage or {}
    try:
        async with SessionLocal() as session:
            await LogService(session).record(
                endpoint=_ENDPOINT,
                status_code=status_code,
                latency_ms=round(latency_ms, 2),
                model_used=model_name,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
            )
            await session.commit()
    except Exception as exc:  # noqa: BLE001 - never fail a request over logging
        logger.warning("Failed to write streaming request log: %s", exc)
