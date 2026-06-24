from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow
from app.db.ids import new_id

if TYPE_CHECKING:
    from app.models.video_source_item import VideoSourceItem


class VideoSource(Base):
    """Nguồn video đầu vào (SPEC 02 §4.1, 10). source_type mở rộng không sửa Workflow/Queue."""

    __tablename__ = "video_sources"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("vsrc"))
    name: Mapped[str] = mapped_column(String(200))
    # direct_url (V1) | google_sheets | csv | folder | google_drive | dropbox | onedrive | …
    source_type: Mapped[str] = mapped_column(String(40), default="direct_url", index=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    item_count: Mapped[int] = mapped_column(Integer, default=0)
    # Tổng số item bị bỏ qua do trùng (dedup) — phục vụ thống kê Duplicate.
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    items: Mapped[list[VideoSourceItem]] = relationship(
        back_populates="source", cascade="all, delete-orphan"
    )
