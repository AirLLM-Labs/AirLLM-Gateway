"""Tests for the dashboard stats endpoint (version, uptime, token totals)."""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS


async def test_stats_includes_version_uptime_and_tokens(client):
    resp = await client.get("/admin/stats", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()

    # Overview fields added in v2.
    assert body["version"]
    assert isinstance(body["uptime_seconds"], int)
    assert body["uptime_seconds"] >= 0
    assert body["total_tokens"] == 0
    assert body["tokens_last_24h"] == 0

    # Pre-existing counters remain present.
    assert "active_models" in body
    assert "avg_latency_ms_24h" in body


async def test_stats_requires_admin(client):
    resp = await client.get("/admin/stats")
    assert resp.status_code == 401
