"""CRUD endpoints for the model registry."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import DbSession
from app.schemas.model import ModelCreate, ModelRead, ModelUpdate
from app.services.model_registry import ModelRegistry

router = APIRouter(prefix="/models")


@router.get("", response_model=list[ModelRead])
async def list_models(db: DbSession) -> list[ModelRead]:
    models = await ModelRegistry(db).list()
    return [ModelRead.model_validate(m) for m in models]


@router.post("", response_model=ModelRead, status_code=status.HTTP_201_CREATED)
async def create_model(data: ModelCreate, db: DbSession) -> ModelRead:
    registry = ModelRegistry(db)
    if await registry.get_by_name(data.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A model named '{data.name}' already exists.",
        )
    model = await registry.create(data)
    return ModelRead.model_validate(model)


@router.put("/{model_id}", response_model=ModelRead)
async def update_model(model_id: int, data: ModelUpdate, db: DbSession) -> ModelRead:
    registry = ModelRegistry(db)
    model = await registry.get(model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model not found.")

    # Guard against renaming onto an existing name.
    if data.name and data.name != model.name:
        if await registry.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A model named '{data.name}' already exists.",
            )

    updated = await registry.update(model, data)
    return ModelRead.model_validate(updated)


@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_model(model_id: int, db: DbSession):
    registry = ModelRegistry(db)
    model = await registry.get(model_id)
    if model is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Model not found.")
    await registry.delete(model)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
