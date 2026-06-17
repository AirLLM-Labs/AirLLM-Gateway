"""Admin endpoint exposing usage analytics (time-series + per-model rollups)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.usage import UsageResponse
from app.services.usage_service import UsageService

router = APIRouter(prefix="/usage")


@router.get("", response_model=UsageResponse)
async def usage(
    db: DbSession, days: int = Query(default=7, ge=1, le=90)
) -> UsageResponse:
    data = await UsageService(db).summary(days=days)
    return UsageResponse(**data)
