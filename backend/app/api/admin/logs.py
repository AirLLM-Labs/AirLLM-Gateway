"""Admin endpoint exposing recent request logs for the dashboard."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbSession
from app.schemas.log import RequestLogRead
from app.services.log_service import LogService

router = APIRouter(prefix="/logs")


@router.get("", response_model=list[RequestLogRead])
async def list_logs(
    db: DbSession, limit: int = Query(default=50, ge=1, le=500)
) -> list[RequestLogRead]:
    logs = await LogService(db).recent(limit=limit)
    return [RequestLogRead.model_validate(entry) for entry in logs]
