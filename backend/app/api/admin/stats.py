"""Admin endpoint exposing aggregate dashboard statistics."""

from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.api.deps import DbSession
from app.core.runtime import uptime_seconds
from app.schemas.log import DashboardStats
from app.services.health_service import HealthService
from app.services.log_service import LogService

router = APIRouter(prefix="/stats")


@router.get("", response_model=DashboardStats)
async def dashboard_stats(db: DbSession) -> DashboardStats:
    health = await HealthService(db).check()
    stats = await LogService(db).dashboard_stats(health=health.status)
    return DashboardStats(
        **stats, version=__version__, uptime_seconds=uptime_seconds()
    )
