"""event level

Revision ID: b2c4e6f80a11
Revises: 793d0effa4d0
Create Date: 2026-06-23 11:40:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c4e6f80a11'
down_revision: str | None = '793d0effa4d0'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'events',
        sa.Column('level', sa.String(length=10), nullable=False, server_default='info'),
    )
    op.create_index('ix_events_level', 'events', ['level'])


def downgrade() -> None:
    op.drop_index('ix_events_level', table_name='events')
    op.drop_column('events', 'level')
