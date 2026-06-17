"""API key generation and hashing utilities.

API keys follow the format ``sk-airllm_<random>``. We only ever persist a
salted hash of the key; the plaintext is shown to the user exactly once at
creation time.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

API_KEY_PREFIX = "sk-airllm_"
_RANDOM_BYTES = 24  # -> 32 url-safe chars


def generate_api_key() -> str:
    """Generate a new plaintext API key string."""
    token = secrets.token_urlsafe(_RANDOM_BYTES)
    return f"{API_KEY_PREFIX}{token}"


def hash_api_key(plaintext: str) -> str:
    """Hash an API key for storage.

    We use SHA-256 rather than a slow KDF on purpose: API keys are
    high-entropy (unlike user passwords), so a fast digest is both safe and
    cheap to verify on every request. The digest is deterministic, which lets
    us look keys up by hash in a single indexed query.
    """
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def verify_api_key(plaintext: str, hashed: str) -> bool:
    """Constant-time comparison of a plaintext key against a stored hash."""
    return hmac.compare_digest(hash_api_key(plaintext), hashed)


def key_preview(plaintext: str) -> str:
    """Return a non-sensitive preview like ``sk-airllm_abcd…wxyz``."""
    if not plaintext.startswith(API_KEY_PREFIX):
        return "****"
    body = plaintext[len(API_KEY_PREFIX):]
    if len(body) <= 8:
        return f"{API_KEY_PREFIX}{'*' * len(body)}"
    return f"{API_KEY_PREFIX}{body[:4]}…{body[-4:]}"
