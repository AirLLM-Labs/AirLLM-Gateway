"""Usage-analytics service.

Computes the time-series and per-model rollups shown on the Usage page. Daily
bucketing is done in Python (rather than a SQL date function) so the same code
runs identically on PostgreSQL and the SQLite test database, and so empty days
are zero-filled for clean charts.
"""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.request_log import RequestLog


class UsageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def summary(self, *, days: int = 7) -> dict:
        today = datetime.now(timezone.utc).date()
        # Inclusive window of `days` calendar days ending today.
        day_keys = [
            (today - timedelta(days=offset)).isoformat()
            for offset in range(days - 1, -1, -1)
        ]
        since = datetime.combine(
            today - timedelta(days=days - 1), time.min, tzinfo=timezone.utc
        )

        daily = await self._daily(day_keys, since)
        per_model = await self._per_model(since)

        return {
            "days": days,
            "requests_this_week": sum(d["requests"] for d in daily),
            "tokens_this_week": sum(d["tokens"] for d in daily),
            "daily": daily,
            "per_model": per_model,
        }

    async def _daily(self, day_keys: list[str], since: datetime) -> list[dict]:
        result = await self.db.execute(
            select(RequestLog.created_at, RequestLog.total_tokens).where(
                RequestLog.created_at >= since
            )
        )
        buckets = {key: {"day": key, "requests": 0, "tokens": 0} for key in day_keys}
        for created_at, tokens in result.all():
            key = created_at.date().isoformat()
            bucket = buckets.get(key)
            if bucket is None:  # outside the zero-filled window; skip defensively
                continue
            bucket["requests"] += 1
            bucket["tokens"] += tokens or 0
        return [buckets[key] for key in day_keys]

    async def _per_model(self, since: datetime) -> list[dict]:
        result = await self.db.execute(
            select(
                RequestLog.model_used,
                func.count(RequestLog.id),
                func.coalesce(func.sum(RequestLog.total_tokens), 0),
                func.coalesce(func.avg(RequestLog.latency_ms), 0.0),
            )
            .where(RequestLog.created_at >= since)
            .group_by(RequestLog.model_used)
        )
        rows = [
            {
                "model": model_used or "unknown",
                "requests": int(requests),
                "tokens": int(tokens),
                "avg_latency_ms": round(float(avg_latency), 2),
            }
            for model_used, requests, tokens, avg_latency in result.all()
        ]
        rows.sort(key=lambda r: r["requests"], reverse=True)
        return rows
