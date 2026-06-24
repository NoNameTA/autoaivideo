"""video_source dedup + sheet row map (write-back)

Revision ID: f1d3b9a7c204
Revises: d8a2b4c6e731
Create Date: 2026-06-24 16:30:00.000000

Bổ sung (additive, KHÔNG sửa cột cũ):
- video_source_items.sheet_row  : số dòng THẬT trong worksheet (map write-back đúng dòng).
- video_source_items.video_id   : id video tách từ URL (dedup ưu tiên 1).
- video_source_items.url_hash   : sha1(url) (dedup fallback khi không có video_id).
- video_sources.duplicate_count : tổng số item bị bỏ qua do trùng (thống kê Duplicate).
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f1d3b9a7c204"
down_revision: str | None = "d8a2b4c6e731"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("video_source_items", sa.Column("sheet_row", sa.Integer(), nullable=True))
    op.add_column("video_source_items", sa.Column("video_id", sa.String(length=120), nullable=True))
    op.add_column("video_source_items", sa.Column("url_hash", sa.String(length=64), nullable=True))
    op.create_index(
        "ix_video_source_items_video_id", "video_source_items", ["source_id", "video_id"]
    )
    op.create_index(
        "ix_video_source_items_url_hash", "video_source_items", ["source_id", "url_hash"]
    )
    op.add_column(
        "video_sources",
        sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("video_sources", "duplicate_count")
    op.drop_index("ix_video_source_items_url_hash", table_name="video_source_items")
    op.drop_index("ix_video_source_items_video_id", table_name="video_source_items")
    op.drop_column("video_source_items", "url_hash")
    op.drop_column("video_source_items", "video_id")
    op.drop_column("video_source_items", "sheet_row")
