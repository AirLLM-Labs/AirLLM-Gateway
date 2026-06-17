"""Schemas for the API key admin endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ApiKeyCreate(BaseModel):
    """Payload for POST /admin/api-keys."""

    name: str = Field(..., min_length=1, max_length=255)


class ApiKeyUpdate(BaseModel):
    """Payload for PATCH /admin/api-keys/{id}. All fields optional."""

    enabled: bool | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)


class ApiKeyRead(BaseModel):
    """An API key as shown in listings (never includes the plaintext)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    preview: str
    enabled: bool
    created_at: datetime
    last_used_at: datetime | None = None


class ApiKeyCreated(ApiKeyRead):
    """Returned exactly once on creation — includes the plaintext key."""

    key: str = Field(..., description="The plaintext key. Shown only once.")
