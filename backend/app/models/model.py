"""Model registry ORM model.

A :class:`Model` row describes one model exposed by the gateway and which
upstream llama.cpp server serves it.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Model(Base, TimestampMixin):
    """A registered model backed by an upstream llama.cpp server."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # The public model id clients reference (e.g. "qwen2.5-coder").
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    # Provider/connector type. Phase 1 only ships "llamacpp".
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="llamacpp")

    # Base URL of the upstream server, e.g. "http://127.0.0.1:8080".
    endpoint_url: Mapped[str] = mapped_column(String(512), nullable=False)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Capability tags, e.g. ["chat"] or ["vision"]. Stored as a JSON array.
    capabilities: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=list
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Model id={self.id} name={self.name!r} provider={self.provider!r}>"
