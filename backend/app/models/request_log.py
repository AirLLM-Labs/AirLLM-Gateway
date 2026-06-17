"""Request log ORM model.

One row is written per proxied request so the dashboard can show traffic,
latency and error rates.
"""

from __future__ import annotations

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class RequestLog(Base, TimestampMixin):
    """A single logged request that passed through the gateway."""

    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    endpoint: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Model id requested by the client (nullable: some requests fail before a
    # model is resolved).
    model_used: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # End-to-end latency in milliseconds.
    latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    status_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Token usage, captured from the upstream's OpenAI-style ``usage`` block.
    # Nullable: not every upstream/response reports usage (e.g. failed requests,
    # or streams where the server doesn't honour ``stream_options``).
    prompt_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # `created_at` (from TimestampMixin) doubles as the request timestamp.

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return (
            f"<RequestLog id={self.id} endpoint={self.endpoint!r} "
            f"status={self.status_code} latency_ms={self.latency_ms:.1f}>"
        )
