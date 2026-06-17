"""Tests for API key management and /v1 authentication."""

from __future__ import annotations

from tests.conftest import ADMIN_HEADERS


async def test_v1_requires_api_key(client):
    resp = await client.get("/v1/models")
    assert resp.status_code == 401


async def test_create_key_then_authenticate(client):
    # Create a key via the admin API.
    created = await client.post(
        "/admin/api-keys", headers=ADMIN_HEADERS, json={"name": "default"}
    )
    assert created.status_code == 201
    body = created.json()
    plaintext = body["key"]
    assert plaintext.startswith("sk-airllm_")
    assert "…" in body["preview"]

    # Listing never returns the plaintext.
    listing = await client.get("/admin/api-keys", headers=ADMIN_HEADERS)
    assert listing.status_code == 200
    assert "key" not in listing.json()[0]

    # The key authenticates /v1 calls.
    ok = await client.get("/v1/models", headers={"Authorization": f"Bearer {plaintext}"})
    assert ok.status_code == 200
    assert ok.json()["object"] == "list"

    # A bogus key is rejected.
    bad = await client.get(
        "/v1/models", headers={"Authorization": "Bearer sk-airllm_nope"}
    )
    assert bad.status_code == 401


async def test_revoke_key_blocks_access(client):
    created = await client.post(
        "/admin/api-keys", headers=ADMIN_HEADERS, json={"name": "temp"}
    )
    key_id = created.json()["id"]
    plaintext = created.json()["key"]

    revoke = await client.delete(f"/admin/api-keys/{key_id}", headers=ADMIN_HEADERS)
    assert revoke.status_code == 204

    after = await client.get(
        "/v1/models", headers={"Authorization": f"Bearer {plaintext}"}
    )
    assert after.status_code == 401


async def test_disable_then_reenable_key(client):
    created = await client.post(
        "/admin/api-keys", headers=ADMIN_HEADERS, json={"name": "toggle"}
    )
    key_id = created.json()["id"]
    plaintext = created.json()["key"]
    auth = {"Authorization": f"Bearer {plaintext}"}

    # Disable → 401.
    patched = await client.patch(
        f"/admin/api-keys/{key_id}", headers=ADMIN_HEADERS, json={"enabled": False}
    )
    assert patched.status_code == 200
    assert patched.json()["enabled"] is False
    assert (await client.get("/v1/models", headers=auth)).status_code == 401

    # Re-enable → works again.
    re = await client.patch(
        f"/admin/api-keys/{key_id}", headers=ADMIN_HEADERS, json={"enabled": True}
    )
    assert re.json()["enabled"] is True
    assert (await client.get("/v1/models", headers=auth)).status_code == 200


async def test_last_used_is_stamped_on_auth(client):
    created = await client.post(
        "/admin/api-keys", headers=ADMIN_HEADERS, json={"name": "tracked"}
    )
    plaintext = created.json()["key"]
    assert created.json()["last_used_at"] is None

    await client.get("/v1/models", headers={"Authorization": f"Bearer {plaintext}"})

    listing = await client.get("/admin/api-keys", headers=ADMIN_HEADERS)
    entry = next(k for k in listing.json() if k["name"] == "tracked")
    assert entry["last_used_at"] is not None


async def test_patch_unknown_key_returns_404(client):
    resp = await client.patch(
        "/admin/api-keys/99999", headers=ADMIN_HEADERS, json={"enabled": False}
    )
    assert resp.status_code == 404
