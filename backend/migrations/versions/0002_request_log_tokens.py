"""request_logs: add token usage columns

Adds nullable ``prompt_tokens`` / ``completion_tokens`` / ``total_tokens`` to
``request_logs`` so the dashboard can report token consumption, plus a composite
index to make per-model / per-day rollups cheap.

Revision ID: 0002_request_log_tokens
Revises: 0001_initial
Create Date: 2026-06-16 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_request_log_tokens"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "request_logs", sa.Column("prompt_tokens", sa.Integer(), nullable=True)
    )
    op.add_column(
        "request_logs", sa.Column("completion_tokens", sa.Integer(), nullable=True)
    )
    op.add_column(
        "request_logs", sa.Column("total_tokens", sa.Integer(), nullable=True)
    )
    # Speeds up the usage analytics queries (group by model / time bucket).
    op.create_index(
        "ix_request_logs_model_created",
        "request_logs",
        ["model_used", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_request_logs_model_created", table_name="request_logs")
    op.drop_column("request_logs", "total_tokens")
    op.drop_column("request_logs", "completion_tokens")
    op.drop_column("request_logs", "prompt_tokens")
