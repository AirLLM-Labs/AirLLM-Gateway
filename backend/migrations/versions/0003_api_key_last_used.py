"""api_keys: add last_used_at

Adds a nullable ``last_used_at`` timestamp, updated on each successful
authentication. (The ``enabled`` column already exists from 0001, so enable/
disable needs no schema change — only an endpoint.)

Revision ID: 0003_api_key_last_used
Revises: 0002_request_log_tokens
Create Date: 2026-06-16 00:00:01.000000
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_api_key_last_used"
down_revision: Union[str, None] = "0002_request_log_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "last_used_at")
