"""GET /v1/models — list models available to authenticated clients.

We return the gateway's enabled registry entries (not the upstream's raw list),
so the dashboard's view of "what models exist" is the single source of truth.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ApiKeyDep, DbSession
from app.schemas.openai import ModelCard, ModelList
from app.services.model_registry import ModelRegistry

router = APIRouter()


@router.get("/models", response_model=ModelList)
async def list_models(db: DbSession, _: ApiKeyDep) -> ModelList:
    models = await ModelRegistry(db).list(enabled_only=True)
    return ModelList(
        data=[
            ModelCard(
                id=m.name,
                created=int(m.created_at.timestamp()) if m.created_at else 0,
                owned_by=m.provider,
            )
            for m in models
        ]
    )
