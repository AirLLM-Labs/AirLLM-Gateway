"""SQLAlchemy declarative base.

All ORM models import :class:`Base` from here. Alembic also imports this module
(via ``app.models``) so that ``Base.metadata`` is fully populated for
autogenerate.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base shared by all models."""


class TimestampMixin:
    """Adds a server-managed ``created_at`` column."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
