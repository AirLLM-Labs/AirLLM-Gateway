"""Request-logging middleware.

Times every ``/v1`` request and persists an entry (endpoint, model, latency,
status code, timestamp) so the dashboard can display recent traffic. We open a
dedicated DB session here because the request-scoped session from ``get_db`` is
already closed by the time the response is produced.

Logging failures are swallowed: telemetry must never break a proxied request.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.log_service import LogService

logger = get_logger(__name__)

# Only proxied inference traffic is logged for the dashboard.
_LOGGED_PREFIXES = ("/v1/",)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if not path.startswith(_LOGGED_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            # Streaming responses persist their own row once the stream drains
            # (the middleware finishes before the body streams), so skip them
            # here to avoid double-logging.
            if not getattr(request.state, "skip_request_log", False):
                latency_ms = (time.perf_counter() - start) * 1000
                await self._record(path, status_code, latency_ms, request.state)

    async def _record(
        self, endpoint: str, status_code: int, latency_ms: float, state
    ) -> None:
        try:
            async with SessionLocal() as session:
                await LogService(session).record(
                    endpoint=endpoint,
                    status_code=status_code,
                    latency_ms=round(latency_ms, 2),
                    model_used=getattr(state, "model_used", None),
                    prompt_tokens=getattr(state, "prompt_tokens", None),
                    completion_tokens=getattr(state, "completion_tokens", None),
                    total_tokens=getattr(state, "total_tokens", None),
                )
                await session.commit()
        except Exception as exc:  # noqa: BLE001 - never fail a request over logging
            logger.warning("Failed to write request log: %s", exc)
