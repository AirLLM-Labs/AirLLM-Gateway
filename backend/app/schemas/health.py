"""Schemas for the /health endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

Status = Literal["ok", "degraded", "down"]


class UpstreamHealth(BaseModel):
    """Health of a single registered llama.cpp server."""

    id: int
    name: str
    endpoint_url: str
    status: Status
    latency_ms: float | None = None
    detail: str | None = None


class HealthResponse(BaseModel):
    """Aggregate health for GET /health."""

    status: Status
    database: Status
    upstreams: list[UpstreamHealth]
