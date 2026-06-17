"""Unit tests for API key generation/hashing helpers."""

from __future__ import annotations

from app.core.security import (
    API_KEY_PREFIX,
    generate_api_key,
    hash_api_key,
    key_preview,
    verify_api_key,
)


def test_generated_key_has_prefix_and_is_unique():
    a = generate_api_key()
    b = generate_api_key()
    assert a.startswith(API_KEY_PREFIX)
    assert b.startswith(API_KEY_PREFIX)
    assert a != b


def test_hash_is_deterministic_and_verifiable():
    key = generate_api_key()
    hashed = hash_api_key(key)
    assert hashed == hash_api_key(key)
    assert len(hashed) == 64  # sha256 hex
    assert verify_api_key(key, hashed)
    assert not verify_api_key("sk-airllm_wrong", hashed)


def test_preview_masks_the_secret():
    key = generate_api_key()
    preview = key_preview(key)
    assert preview.startswith(API_KEY_PREFIX)
    assert "…" in preview
    assert key not in preview
