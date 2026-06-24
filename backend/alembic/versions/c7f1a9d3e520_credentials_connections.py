"""credentials + connections (Cloud Adapter)

Revision ID: c7f1a9d3e520
Revises: b2c4e6f80a11
Create Date: 2026-06-23 13:10:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'c7f1a9d3e520'
down_revision: str | None = 'b2c4e6f80a11'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'credentials',
        sa.Column('id', sa.String(length=40), nullable=False),
        sa.Column('provider', sa.String(length=60), nullable=False),
        sa.Column('connection_name', sa.String(length=120), nullable=False),
        sa.Column('authentication_type', sa.String(length=40), nullable=False),
        sa.Column('encrypted_secret', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_credentials_provider', 'credentials', ['provider'])

    op.create_table(
        'connections',
        sa.Column('id', sa.String(length=40), nullable=False),
        sa.Column('provider', sa.String(length=60), nullable=False),
        sa.Column('credential_id', sa.String(length=40), nullable=True),
        sa.Column('display_name', sa.String(length=160), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('health_status', sa.String(length=20), nullable=False),
        sa.Column('last_check', sa.DateTime(timezone=True), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=False),
        sa.Column('settings', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['credential_id'], ['credentials.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_connections_provider', 'connections', ['provider'])


def downgrade() -> None:
    op.drop_index('ix_connections_provider', table_name='connections')
    op.drop_table('connections')
    op.drop_index('ix_credentials_provider', table_name='credentials')
    op.drop_table('credentials')
