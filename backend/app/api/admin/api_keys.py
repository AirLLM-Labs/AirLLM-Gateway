"""Admin endpoints for managing API keys."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import DbSession
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
    ApiKeyUpdate,
)
from app.services.api_key_service import ApiKeyService

router = APIRouter(prefix="/api-keys")


@router.get("", response_model=list[ApiKeyRead])
async def list_api_keys(db: DbSession) -> list[ApiKeyRead]:
    keys = await ApiKeyService(db).list()
    return [ApiKeyRead.model_validate(k) for k in keys]


@router.post("", response_model=ApiKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(data: ApiKeyCreate, db: DbSession) -> ApiKeyCreated:
    record, plaintext = await ApiKeyService(db).create(data.name)
    # The plaintext is included here and nowhere else.
    return ApiKeyCreated(
        id=record.id,
        name=record.name,
        preview=record.preview,
        enabled=record.enabled,
        created_at=record.created_at,
        key=plaintext,
    )


@router.patch("/{key_id}", response_model=ApiKeyRead)
async def update_api_key(
    key_id: int, data: ApiKeyUpdate, db: DbSession
) -> ApiKeyRead:
    service = ApiKeyService(db)
    record = await service.get(key_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found.")
    if data.enabled is not None:
        record = await service.set_enabled(record, data.enabled)
    if data.name is not None:
        record = await service.rename(record, data.name)
    return ApiKeyRead.model_validate(record)


@router.delete(
    "/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_api_key(key_id: int, db: DbSession):
    service = ApiKeyService(db)
    record = await service.get(key_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "API key not found.")
    await service.delete(record)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
