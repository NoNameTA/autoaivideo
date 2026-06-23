from __future__ import annotations

from sqlalchemy import JSON, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin
from app.db.ids import new_id


class Pipeline(Base, TimestampMixin):
    """Pipeline/workflow người dùng tạo/sửa (SPEC 02 §4). steps=[{step_key,adapter,config}]."""

    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("pipe"))
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")
    steps: Mapped[list] = mapped_column(JSON, default=list)
    builtin: Mapped[bool] = mapped_column(Boolean, default=False)
