from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.db.ids import new_id


class Connection(Base):
    """Connection Manager — kết nối có cấu hình tới 1 Cloud Adapter (SPEC 10, 06 §10).

    KHÔNG chứa bí mật (chỉ trỏ `credential_id`). `settings` phi-bí-mật (vd spreadsheet_id).
    """

    __tablename__ = "connections"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("conn"))
    provider: Mapped[str] = mapped_column(String(60), index=True)
    credential_id: Mapped[str | None] = mapped_column(
        ForeignKey("credentials.id", ondelete="SET NULL"), default=None
    )
    display_name: Mapped[str] = mapped_column(String(160))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    health_status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_check: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
