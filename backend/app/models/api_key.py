"""API key ORM model.

Only a SHA-256 hash of the key is stored. A short non-sensitive preview is
persisted so the dashboard can display which key is which without ever holding
the plaintext.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ApiKey(Base, TimestampMixin):
    """An API key that authenticates calls to the /v1 endpoints."""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Deterministic SHA-256 hex digest of the plaintext key. Unique + indexed
    # so authentication is a single lookup.
    hashed_key: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    # Non-sensitive display preview, e.g. "sk-airllm_abcd…wxyz".
    preview: Mapped[str] = mapped_column(String(64), nullable=False, default="")

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Updated on each successful authentication so the dashboard can show which
    # keys are actually in use. Nullable: a freshly created key has never been
    # used.
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ApiKey id={self.id} name={self.name!r} enabled={self.enabled}>"
