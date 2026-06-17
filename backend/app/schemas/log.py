"""Schemas for request-log readouts and dashboard stats."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RequestLogRead(BaseModel):
    """A single request-log row for the dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    endpoint: str
    model_used: str | None
    latency_ms: float
    status_code: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    created_at: datetime


class DashboardStats(BaseModel):
    """Aggregate counters shown on the dashboard landing page."""

    active_models: int
    total_models: int
    api_keys: int
    total_requests: int
    requests_last_24h: int
    error_rate_24h: float
    avg_latency_ms_24h: float
    total_tokens: int
    tokens_last_24h: int
    version: str
    uptime_seconds: int
    health: str
