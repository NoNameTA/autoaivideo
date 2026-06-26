"""video_source_items.media_type (Media Check sau Download)

Revision ID: a1b2c3d4e5f6
Revises: f1d3b9a7c204
Create Date: 2026-06-26 12:00:00.000000

Bổ sung (additive, KHÔNG sửa cột cũ):
- video_source_items.media_type : video | audio_only | invalid | NULL (chưa kiểm).
  Phân loại theo STREAM THẬT bằng ffprobe (KHÔNG theo đuôi/tên file).
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f1d3b9a7c204"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("video_source_items", sa.Column("media_type", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("video_source_items", "media_type")
