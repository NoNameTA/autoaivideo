from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, utcnow
from app.db.ids import new_id

if TYPE_CHECKING:
    from app.models.video_source import VideoSource


class VideoSourceItem(Base):
    """1 link video trong 1 Video Source (SPEC 10). status suy từ job đã link khi đọc."""

    __tablename__ = "video_source_items"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("vitem"))
    source_id: Mapped[str] = mapped_column(
        ForeignKey("video_sources.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, default=0)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(300), default=None)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    job_id: Mapped[str | None] = mapped_column(
        ForeignKey("jobs.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    source: Mapped[VideoSource] = relationship(back_populates="items")
