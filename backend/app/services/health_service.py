"""Health-check service.

Aggregates database connectivity and the reachability of every registered
llama.cpp server into a single status payload.
"""

from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.schemas.health import HealthResponse, UpstreamHealth
from app.services.http_client import get_http_client
from app.services.llamacpp import LlamaCppConnector
from app.services.model_registry import ModelRegistry

logger = get_logger(__name__)


class HealthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check(self) -> HealthResponse:
        database = await self._check_database()
        upstreams = await self._check_upstreams()

        # Roll up an overall status.
        if database == "down":
            overall = "down"
        elif any(u.status == "down" for u in upstreams) or not upstreams:
            overall = "degraded" if database == "ok" else "down"
        else:
            overall = "ok"

        return HealthResponse(
            status=overall, database=database, upstreams=upstreams
        )

    async def _check_database(self) -> str:
        try:
            await self.db.execute(text("SELECT 1"))
            return "ok"
        except Exception as exc:  # noqa: BLE001 - report any failure as down
            logger.error("Database health check failed: %s", exc)
            return "down"

    async def _check_upstreams(self) -> list[UpstreamHealth]:
        registry = ModelRegistry(self.db)
        models = await registry.list()
        if not models:
            return []

        connector = LlamaCppConnector(get_http_client())

        async def probe(model) -> UpstreamHealth:
            ok, latency, detail = await connector.ping(model.endpoint_url)
            return UpstreamHealth(
                id=model.id,
                name=model.name,
                endpoint_url=model.endpoint_url,
                status="ok" if ok else "down",
                latency_ms=round(latency, 2) if latency is not None else None,
                detail=detail,
            )

        return list(await asyncio.gather(*(probe(m) for m in models)))
