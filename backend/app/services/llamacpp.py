"""llama.cpp connector.

llama.cpp's ``server`` binary already speaks an OpenAI-compatible dialect on
``/v1/chat/completions`` and ``/v1/models``. This connector is therefore a thin
proxy: it forwards requests, streams Server-Sent Events back unchanged, and
exposes health/model-discovery helpers. Keeping a single shared
:class:`httpx.AsyncClient` lets us pool connections across requests.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class UpstreamError(Exception):
    """Raised when an upstream llama.cpp server cannot be reached or errors.

    ``status_code`` is the HTTP status to surface to the client; ``payload`` is
    an OpenAI-style error body.
    """

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    def as_openai_error(self) -> dict[str, Any]:
        return {
            "error": {
                "message": self.message,
                "type": "upstream_error",
                "code": self.status_code,
            }
        }


class LlamaCppConnector:
    """Stateless helper for talking to llama.cpp servers."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    # ----------------------------------------------------------------- #
    # Discovery / health
    # ----------------------------------------------------------------- #

    async def list_models(self, endpoint_url: str) -> list[str]:
        """Return the model ids advertised by an upstream's GET /v1/models."""
        url = f"{endpoint_url.rstrip('/')}/v1/models"
        try:
            resp = await self._client.get(url, timeout=settings.health_timeout)
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Model discovery failed for %s: %s", url, exc)
            return []
        data = resp.json().get("data", [])
        return [item.get("id", "") for item in data if item.get("id")]

    async def ping(self, endpoint_url: str) -> tuple[bool, float | None, str | None]:
        """Probe an upstream's /health endpoint.

        Returns ``(ok, latency_ms, detail)``. llama.cpp exposes ``/health``;
        a 200 means the model is loaded and ready.
        """
        url = f"{endpoint_url.rstrip('/')}/health"
        try:
            resp = await self._client.get(url, timeout=settings.health_timeout)
        except httpx.HTTPError as exc:
            return False, None, str(exc)
        latency_ms = resp.elapsed.total_seconds() * 1000
        if resp.status_code == 200:
            return True, latency_ms, None
        return False, latency_ms, f"HTTP {resp.status_code}"

    # ----------------------------------------------------------------- #
    # Chat completions
    # ----------------------------------------------------------------- #

    async def chat_completion(
        self, endpoint_url: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Forward a non-streaming chat completion and return the JSON body."""
        url = f"{endpoint_url.rstrip('/')}/v1/chat/completions"
        try:
            resp = await self._client.post(
                url, json=payload, timeout=settings.upstream_timeout
            )
        except httpx.HTTPError as exc:
            raise UpstreamError(502, f"Failed to reach upstream: {exc}") from exc

        if resp.status_code >= 400:
            raise UpstreamError(
                resp.status_code,
                _extract_error(resp) or f"Upstream returned HTTP {resp.status_code}",
            )
        return resp.json()

    async def chat_completion_stream(
        self, endpoint_url: str, payload: dict[str, Any]
    ) -> AsyncIterator[bytes]:
        """Forward a streaming chat completion, yielding raw SSE chunks.

        llama.cpp already emits OpenAI-style ``data: {...}`` SSE lines ending
        with ``data: [DONE]``, so we pass the bytes through untouched.
        """
        url = f"{endpoint_url.rstrip('/')}/v1/chat/completions"
        payload = {**payload, "stream": True}
        try:
            async with self._client.stream(
                "POST", url, json=payload, timeout=settings.upstream_timeout
            ) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    raise UpstreamError(
                        resp.status_code,
                        _decode_error(body)
                        or f"Upstream returned HTTP {resp.status_code}",
                    )
                async for chunk in resp.aiter_bytes():
                    if chunk:
                        yield chunk
        except httpx.HTTPError as exc:
            raise UpstreamError(502, f"Failed to reach upstream: {exc}") from exc


def _extract_error(resp: httpx.Response) -> str | None:
    try:
        body = resp.json()
    except ValueError:
        return resp.text or None
    if isinstance(body, dict):
        err = body.get("error")
        if isinstance(err, dict):
            return err.get("message")
        if isinstance(err, str):
            return err
    return None


def _decode_error(body: bytes) -> str | None:
    import json

    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return body.decode("utf-8", "replace") or None
    if isinstance(data, dict):
        err = data.get("error")
        if isinstance(err, dict):
            return err.get("message")
        if isinstance(err, str):
            return err
    return None
