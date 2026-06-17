"""Tests for the /health endpoint."""

from __future__ import annotations


async def test_health_ok_with_no_upstreams(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["database"] == "ok"
    # With no registered upstreams the gateway is up but reports "degraded".
    assert body["status"] in {"ok", "degraded"}
    assert body["upstreams"] == []


async def test_root_metadata(client):
    resp = await client.get("/")
    assert resp.status_code == 200
    assert resp.json()["health"] == "/health"
