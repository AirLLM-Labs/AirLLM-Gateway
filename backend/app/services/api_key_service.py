"""API key service.

Generates keys, persists their hashes, and authenticates incoming requests.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_api_key, hash_api_key, key_preview
from app.models.api_key import ApiKey


class ApiKeyService:
    """CRUD + authentication for API keys."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self) -> list[ApiKey]:
        result = await self.db.execute(select(ApiKey).order_by(ApiKey.id))
        return list(result.scalars().all())

    async def get(self, key_id: int) -> ApiKey | None:
        return await self.db.get(ApiKey, key_id)

    async def create(self, name: str) -> tuple[ApiKey, str]:
        """Create a key, returning ``(row, plaintext)``.

        The plaintext is returned to the caller exactly once and never stored.
        """
        plaintext = generate_api_key()
        record = ApiKey(
            name=name,
            hashed_key=hash_api_key(plaintext),
            preview=key_preview(plaintext),
            enabled=True,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return record, plaintext

    async def delete(self, record: ApiKey) -> None:
        await self.db.delete(record)
        await self.db.flush()

    async def set_enabled(self, record: ApiKey, enabled: bool) -> ApiKey:
        """Enable or disable a key."""
        record.enabled = enabled
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def rename(self, record: ApiKey, name: str) -> ApiKey:
        record.name = name
        await self.db.flush()
        await self.db.refresh(record)
        return record

    async def authenticate(self, plaintext: str) -> ApiKey | None:
        """Return the enabled key matching ``plaintext``, or ``None``.

        Stamps ``last_used_at`` on success so the dashboard can show usage.
        """
        hashed = hash_api_key(plaintext)
        result = await self.db.execute(
            select(ApiKey).where(
                ApiKey.hashed_key == hashed, ApiKey.enabled.is_(True)
            )
        )
        record = result.scalar_one_or_none()
        if record is not None:
            record.last_used_at = datetime.now(timezone.utc)
            await self.db.flush()
        return record

    async def count(self) -> int:
        from sqlalchemy import func

        result = await self.db.execute(select(func.count(ApiKey.id)))
        return int(result.scalar_one())
