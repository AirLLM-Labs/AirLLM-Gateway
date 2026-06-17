"""Model registry service.

Encapsulates all database access for :class:`~app.models.model.Model` so the
API layer stays thin. Also resolves which upstream serves a given model id for
the chat-completions proxy.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model import Model
from app.schemas.model import ModelCreate, ModelUpdate


class ModelRegistry:
    """CRUD + lookup helpers for registered models."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(self, *, enabled_only: bool = False) -> list[Model]:
        stmt = select(Model).order_by(Model.id)
        if enabled_only:
            stmt = stmt.where(Model.enabled.is_(True))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get(self, model_id: int) -> Model | None:
        return await self.db.get(Model, model_id)

    async def get_by_name(self, name: str) -> Model | None:
        result = await self.db.execute(select(Model).where(Model.name == name))
        return result.scalar_one_or_none()

    async def resolve_enabled(self, name: str) -> Model | None:
        """Return an enabled model by name, for request routing."""
        result = await self.db.execute(
            select(Model).where(Model.name == name, Model.enabled.is_(True))
        )
        return result.scalar_one_or_none()

    async def create(self, data: ModelCreate) -> Model:
        model = Model(
            name=data.name,
            provider=data.provider,
            endpoint_url=data.endpoint_url,
            enabled=data.enabled,
            capabilities=data.capabilities,
        )
        self.db.add(model)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def update(self, model: Model, data: ModelUpdate) -> Model:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(model, field, value)
        await self.db.flush()
        await self.db.refresh(model)
        return model

    async def delete(self, model: Model) -> None:
        await self.db.delete(model)
        await self.db.flush()
