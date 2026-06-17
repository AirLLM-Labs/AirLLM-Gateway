"""GET /health — unauthenticated liveness/readiness probe.

Returns the DB status and the reachability of every registered llama.cpp
server. HTTP 200 when overall status is ``ok`` or ``degraded`` (the gateway is
up even if an upstream is down); 503 when the database is ``down``.
"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.deps import DbSession
from app.schemas.health import HealthResponse
from app.services.health_service import HealthService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(db: DbSession):
    result: HealthResponse = await HealthService(db).check()
    status_code = 503 if result.status == "down" else 200
    return JSONResponse(status_code=status_code, content=result.model_dump())
