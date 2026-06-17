"""Shared httpx.AsyncClient lifecycle.

A single pooled client is created on app startup and reused for every upstream
call (connector + health checks), then closed on shutdown.
"""

from __future__ import annotations

import httpx

_client: httpx.AsyncClient | None = None


async def startup_http_client() -> None:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )


async def shutdown_http_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def get_http_client() -> httpx.AsyncClient:
    """Return the shared client, creating a lazy one if needed (e.g. in tests)."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient()
    return _client
