"""Request logging + dashboard statistics service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.model import Model
from app.models.request_log import RequestLog


class LogService:
    """Persists request logs and computes dashboard aggregates."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def record(
        self,
        *,
        endpoint: str,
        status_code: int,
        latency_ms: float,
        model_used: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> RequestLog:
        entry = RequestLog(
            endpoint=endpoint,
            status_code=status_code,
            latency_ms=latency_ms,
            model_used=model_used,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def recent(self, limit: int = 50) -> list[RequestLog]:
        result = await self.db.execute(
            select(RequestLog).order_by(RequestLog.id.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def dashboard_stats(self, *, health: str) -> dict:
        """Compute the aggregate counters shown on the dashboard."""
        since = datetime.now(timezone.utc) - timedelta(hours=24)

        total_models = await self._scalar(select(func.count(Model.id)))
        active_models = await self._scalar(
            select(func.count(Model.id)).where(Model.enabled.is_(True))
        )
        api_keys = await self._scalar(select(func.count(ApiKey.id)))
        total_requests = await self._scalar(select(func.count(RequestLog.id)))

        requests_24h = await self._scalar(
            select(func.count(RequestLog.id)).where(RequestLog.created_at >= since)
        )
        errors_24h = await self._scalar(
            select(func.count(RequestLog.id)).where(
                RequestLog.created_at >= since, RequestLog.status_code >= 400
            )
        )
        avg_latency = await self._scalar(
            select(func.coalesce(func.avg(RequestLog.latency_ms), 0.0)).where(
                RequestLog.created_at >= since
            ),
            cast=float,
        )

        total_tokens = await self._scalar(
            select(func.coalesce(func.sum(RequestLog.total_tokens), 0))
        )
        tokens_24h = await self._scalar(
            select(func.coalesce(func.sum(RequestLog.total_tokens), 0)).where(
                RequestLog.created_at >= since
            )
        )

        error_rate = (errors_24h / requests_24h) if requests_24h else 0.0

        return {
            "active_models": active_models,
            "total_models": total_models,
            "api_keys": api_keys,
            "total_requests": total_requests,
            "requests_last_24h": requests_24h,
            "error_rate_24h": round(error_rate, 4),
            "avg_latency_ms_24h": round(float(avg_latency), 2),
            "total_tokens": total_tokens,
            "tokens_last_24h": tokens_24h,
            "health": health,
        }

    async def _scalar(self, stmt, *, cast=int):
        result = await self.db.execute(stmt)
        value = result.scalar_one()
        return cast(value) if value is not None else cast(0)
