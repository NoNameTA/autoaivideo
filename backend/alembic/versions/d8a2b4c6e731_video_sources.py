"""video_sources + video_source_items

Revision ID: d8a2b4c6e731
Revises: c7f1a9d3e520
Create Date: 2026-06-24 09:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd8a2b4c6e731'
down_revision: str | None = 'c7f1a9d3e520'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'video_sources',
        sa.Column('id', sa.String(length=40), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('source_type', sa.String(length=40), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('item_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_video_sources_source_type', 'video_sources', ['source_type'])

    op.create_table(
        'video_source_items',
        sa.Column('id', sa.String(length=40), nullable=False),
        sa.Column('source_id', sa.String(length=40), nullable=False),
        sa.Column('seq', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('job_id', sa.String(length=40), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['video_sources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_video_source_items_source_id', 'video_source_items', ['source_id'])


def downgrade() -> None:
    op.drop_index('ix_video_source_items_source_id', table_name='video_source_items')
    op.drop_table('video_source_items')
    op.drop_index('ix_video_sources_source_type', table_name='video_sources')
    op.drop_table('video_sources')
