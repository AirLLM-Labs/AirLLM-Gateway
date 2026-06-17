"""initial schema: models, api_keys, request_logs

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-15 00:00:00.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("endpoint_url", sa.String(length=512), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("capabilities", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_models_name", "models", ["name"], unique=True)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hashed_key", sa.String(length=64), nullable=False),
        sa.Column("preview", sa.String(length=64), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_hashed_key", "api_keys", ["hashed_key"], unique=True)

    op.create_table(
        "request_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("endpoint", sa.String(length=255), nullable=False),
        sa.Column("model_used", sa.String(length=255), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_request_logs_endpoint", "request_logs", ["endpoint"])
    op.create_index("ix_request_logs_status_code", "request_logs", ["status_code"])


def downgrade() -> None:
    op.drop_index("ix_request_logs_status_code", table_name="request_logs")
    op.drop_index("ix_request_logs_endpoint", table_name="request_logs")
    op.drop_table("request_logs")

    op.drop_index("ix_api_keys_hashed_key", table_name="api_keys")
    op.drop_table("api_keys")

    op.drop_index("ix_models_name", table_name="models")
    op.drop_table("models")
