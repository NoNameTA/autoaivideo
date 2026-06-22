from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_PIPELINE
from app.db.base import Base, TimestampMixin
from app.db.ids import new_id

if TYPE_CHECKING:
    from app.models.batch import Batch


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("proj"))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    default_pipeline: Mapped[str] = mapped_column(String(100), default=DEFAULT_PIPELINE)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    batches: Mapped[list[Batch]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
