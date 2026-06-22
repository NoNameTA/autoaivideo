from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.ids import new_id


class AllowedFolder(Base, TimestampMixin):
    """Thư mục được cấp quyền cho File Manager (SPEC 11 §5). Nguồn chân lý ở DB, đẩy xuống agent."""

    __tablename__ = "allowed_folders"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("fold"))
    path: Mapped[str] = mapped_column(String(500), unique=True)
    label: Mapped[str] = mapped_column(String(200), default="")
