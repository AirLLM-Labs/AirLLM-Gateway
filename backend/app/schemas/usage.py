"""Schemas for the usage-analytics endpoint."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UsageDaily(BaseModel):
    """One calendar-day bucket of traffic."""

    day: str  # ISO date, e.g. "2026-06-16"
    requests: int
    tokens: int


class UsagePerModel(BaseModel):
    """Aggregate traffic for a single model over the window."""

    # `model` would collide with Pydantic's protected namespace otherwise.
    model_config = ConfigDict(protected_namespaces=())

    model: str
    requests: int
    tokens: int
    avg_latency_ms: float


class UsageResponse(BaseModel):
    """Response body for GET /admin/usage."""

    days: int
    requests_this_week: int
    tokens_this_week: int
    daily: list[UsageDaily]
    per_model: list[UsagePerModel]
