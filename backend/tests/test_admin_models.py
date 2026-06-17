"""Tests for the model registry admin CRUD endpoints."""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS


async def test_models_require_admin(client):
    resp = await client.get("/admin/models")
    assert resp.status_code == 401


async def test_model_crud_lifecycle(client):
    # Create.
    resp = await client.post(
        "/admin/models",
        headers=ADMIN_HEADERS,
        json={
            "name": "coder",
            "endpoint_url": "http://127.0.0.1:8080/",
            "capabilities": ["chat"],
        },
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["name"] == "coder"
    assert created["endpoint_url"] == "http://127.0.0.1:8080"  # trailing slash stripped
    assert created["provider"] == "llamacpp"
    model_id = created["id"]

    # Duplicate name -> 409.
    dup = await client.post(
        "/admin/models",
        headers=ADMIN_HEADERS,
        json={"name": "coder", "endpoint_url": "http://x"},
    )
    assert dup.status_code == 409

    # List.
    listing = await client.get("/admin/models", headers=ADMIN_HEADERS)
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    # Update.
    upd = await client.put(
        f"/admin/models/{model_id}",
        headers=ADMIN_HEADERS,
        json={"enabled": False},
    )
    assert upd.status_code == 200
    assert upd.json()["enabled"] is False

    # Delete.
    dele = await client.delete(f"/admin/models/{model_id}", headers=ADMIN_HEADERS)
    assert dele.status_code == 204

    # Gone.
    missing = await client.put(
        f"/admin/models/{model_id}", headers=ADMIN_HEADERS, json={"enabled": True}
    )
    assert missing.status_code == 404
