"""Shared FastAPI dependencies.

Provides:
* ``get_db`` (re-exported) — an async DB session.
* ``require_api_key`` — authenticates ``/v1`` callers via ``Authorization:
  Bearer sk-airllm_...`` and returns the matching :class:`ApiKey`.
* ``require_admin`` — protects ``/admin`` endpoints with the shared admin token.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.api_key import ApiKey
from app.services.api_key_service import ApiKeyService

settings = get_settings()

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _extract_bearer(authorization: str | None) -> str | None:
    """Pull the token out of an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    # Some clients send the raw key; accept it too.
    return authorization.strip()


async def require_api_key(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> ApiKey:
    """Authenticate a /v1 request and return the API key record."""
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Pass 'Authorization: Bearer sk-airllm_...'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    key = await ApiKeyService(db).authenticate(token)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or disabled API key.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return key


async def require_admin(
    authorization: Annotated[str | None, Header()] = None,
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    """Guard /admin endpoints with the shared admin token.

    Accepts the token either as ``Authorization: Bearer <token>`` or as the
    ``X-Admin-Token`` header (used by the dashboard's server-side proxy).
    """
    token = x_admin_token or _extract_bearer(authorization)
    if not token or token != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required.",
        )


ApiKeyDep = Annotated[ApiKey, Depends(require_api_key)]
AdminDep = Annotated[None, Depends(require_admin)]
