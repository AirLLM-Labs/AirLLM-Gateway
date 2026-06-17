"""Schemas for the model registry admin API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ModelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    provider: str = Field(default="llamacpp", max_length=64)
    endpoint_url: str = Field(..., min_length=1, max_length=512)
    enabled: bool = True
    capabilities: list[str] = Field(default_factory=lambda: ["chat"])

    @field_validator("endpoint_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


class ModelCreate(ModelBase):
    """Payload for POST /admin/models."""


class ModelUpdate(BaseModel):
    """Payload for PUT /admin/models/{id}. All fields optional (partial update)."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    provider: str | None = Field(default=None, max_length=64)
    endpoint_url: str | None = Field(default=None, min_length=1, max_length=512)
    enabled: bool | None = None
    capabilities: list[str] | None = None

    @field_validator("endpoint_url")
    @classmethod
    def _strip_trailing_slash(cls, v: str | None) -> str | None:
        return v.rstrip("/") if v is not None else v


class ModelRead(ModelBase):
    """Representation returned by the admin API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
