"""Admin router package (model registry, API keys, logs, stats).

Every route here is protected by the shared admin token via ``require_admin``.
"""

from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.api.admin import api_keys, logs, models, stats, usage

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
router.include_router(models.router)
router.include_router(api_keys.router)
router.include_router(logs.router)
router.include_router(stats.router)
router.include_router(usage.router)
