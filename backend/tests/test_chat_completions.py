"""Tests for the chat-completions proxy (with a mocked upstream connector)."""

from __future__ import annotations

import pytest

from app.services import llamacpp
from tests.conftest import ADMIN_HEADERS


@pytest.fixture
async def authed(client):
    """Register a model + API key; return (client, headers)."""
    await client.post(
        "/admin/models",
        headers=ADMIN_HEADERS,
        json={"name": "coder", "endpoint_url": "http://127.0.0.1:8080"},
    )
    created = await client.post(
        "/admin/api-keys", headers=ADMIN_HEADERS, json={"name": "k"}
    )
    key = created.json()["key"]
    return client, {"Authorization": f"Bearer {key}"}


async def test_non_streaming_chat(authed, monkeypatch):
    client, headers = authed

    async def fake_completion(self, endpoint_url, payload):
        assert endpoint_url == "http://127.0.0.1:8080"
        return {
            "id": "chatcmpl-1",
            "object": "chat.completion",
            "created": 0,
            "model": payload["model"],
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "hello!"},
                    "finish_reason": "stop",
                }
            ],
        }

    monkeypatch.setattr(llamacpp.LlamaCppConnector, "chat_completion", fake_completion)

    resp = await client.post(
        "/v1/chat/completions",
        headers=headers,
        json={"model": "coder", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 200
    assert resp.json()["choices"][0]["message"]["content"] == "hello!"


async def test_unknown_model_returns_404(authed):
    client, headers = authed
    resp = await client.post(
        "/v1/chat/completions",
        headers=headers,
        json={"model": "does-not-exist", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["type"] == "model_not_found"


async def test_streaming_chat(authed, monkeypatch):
    client, headers = authed

    async def fake_stream(self, endpoint_url, payload):
        yield b'data: {"choices":[{"delta":{"content":"he"}}]}\n\n'
        yield b'data: {"choices":[{"delta":{"content":"llo"}}]}\n\n'
        yield b"data: [DONE]\n\n"

    monkeypatch.setattr(
        llamacpp.LlamaCppConnector, "chat_completion_stream", fake_stream
    )

    async with client.stream(
        "POST",
        "/v1/chat/completions",
        headers=headers,
        json={
            "model": "coder",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = b""
        async for chunk in resp.aiter_bytes():
            body += chunk

    assert b"[DONE]" in body
    # Both upstream deltas were forwarded verbatim.
    assert b'"content":"he"' in body
    assert b'"content":"llo"' in body


async def test_requests_are_logged(authed, monkeypatch):
    client, headers = authed

    async def fake_completion(self, endpoint_url, payload):
        return {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "coder",
            "choices": [],
        }

    monkeypatch.setattr(llamacpp.LlamaCppConnector, "chat_completion", fake_completion)

    await client.post(
        "/v1/chat/completions",
        headers=headers,
        json={"model": "coder", "messages": [{"role": "user", "content": "hi"}]},
    )

    logs = await client.get("/admin/logs", headers=ADMIN_HEADERS)
    assert logs.status_code == 200
    entries = logs.json()
    assert any(e["endpoint"] == "/v1/chat/completions" for e in entries)
    assert any(e["model_used"] == "coder" for e in entries)


async def test_non_streaming_records_token_usage(authed, monkeypatch):
    client, headers = authed

    async def fake_completion(self, endpoint_url, payload):
        return {
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "coder",
            "choices": [],
            "usage": {"prompt_tokens": 7, "completion_tokens": 11, "total_tokens": 18},
        }

    monkeypatch.setattr(llamacpp.LlamaCppConnector, "chat_completion", fake_completion)

    await client.post(
        "/v1/chat/completions",
        headers=headers,
        json={"model": "coder", "messages": [{"role": "user", "content": "hi"}]},
    )

    entries = (await client.get("/admin/logs", headers=ADMIN_HEADERS)).json()
    logged = next(e for e in entries if e["endpoint"] == "/v1/chat/completions")
    assert logged["prompt_tokens"] == 7
    assert logged["completion_tokens"] == 11
    assert logged["total_tokens"] == 18


async def test_streaming_records_token_usage(authed, monkeypatch):
    client, headers = authed

    async def fake_stream(self, endpoint_url, payload):
        # The gateway should have asked for usage.
        assert payload.get("stream_options") == {"include_usage": True}
        yield b'data: {"choices":[{"delta":{"content":"hi"}}]}\n\n'
        yield (
            b'data: {"choices":[],"usage":'
            b'{"prompt_tokens":3,"completion_tokens":5,"total_tokens":8}}\n\n'
        )
        yield b"data: [DONE]\n\n"

    monkeypatch.setattr(
        llamacpp.LlamaCppConnector, "chat_completion_stream", fake_stream
    )

    async with client.stream(
        "POST",
        "/v1/chat/completions",
        headers=headers,
        json={
            "model": "coder",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
    ) as resp:
        assert resp.status_code == 200
        async for _ in resp.aiter_bytes():
            pass

    entries = (await client.get("/admin/logs", headers=ADMIN_HEADERS)).json()
    # Exactly one row for the streamed request (no double-logging).
    streamed = [e for e in entries if e["endpoint"] == "/v1/chat/completions"]
    assert len(streamed) == 1
    assert streamed[0]["total_tokens"] == 8
    assert streamed[0]["completion_tokens"] == 5
