"""Tests for the usage-analytics endpoint."""

from __future__ import annotations

import pytest

from app.services import llamacpp
from tests.conftest import ADMIN_HEADERS


@pytest.fixture
async def authed(client):
    await client.post(
        "/admin/models",
        headers=ADMIN_HEADERS,
        json={"name": "coder", "endpoint_url": "http://127.0.0.1:8080"},
    )
    created = await client.post(
        "/admin/api-keys", headers=ADMIN_HEADERS, json={"name": "k"}
    )
    return client, {"Authorization": f"Bearer {created.json()['key']}"}


async def test_usage_empty(client):
    resp = await client.get("/admin/usage", headers=ADMIN_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["days"] == 7
    assert len(body["daily"]) == 7  # zero-filled week
    assert body["requests_this_week"] == 0
    assert body["per_model"] == []


async def test_usage_reflects_traffic(authed, monkeypatch):
    client, headers = authed

    async def fake_completion(self, endpoint_url, payload):
        return {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "coder",
            "choices": [],
            "usage": {"prompt_tokens": 4, "completion_tokens": 6, "total_tokens": 10},
        }

    monkeypatch.setattr(llamacpp.LlamaCppConnector, "chat_completion", fake_completion)

    for _ in range(3):
        await client.post(
            "/v1/chat/completions",
            headers=headers,
            json={"model": "coder", "messages": [{"role": "user", "content": "hi"}]},
        )

    body = (await client.get("/admin/usage", headers=ADMIN_HEADERS)).json()
    assert body["requests_this_week"] == 3
    assert body["tokens_this_week"] == 30
    # Today's bucket (last entry) carries the traffic.
    assert body["daily"][-1]["requests"] == 3
    assert body["daily"][-1]["tokens"] == 30

    coder = next(m for m in body["per_model"] if m["model"] == "coder")
    assert coder["requests"] == 3
    assert coder["tokens"] == 30
