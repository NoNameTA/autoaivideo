from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.ids import new_id
from app.models.enums import BatchStatus

if TYPE_CHECKING:
    from app.models.job import Job
    from app.models.project import Project


class Batch(Base, TimestampMixin):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("batch"))
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    status: Mapped[BatchStatus] = mapped_column(String(20), default=BatchStatus.created)
    input_count: Mapped[int] = mapped_column(Integer, default=0)
    counts: Mapped[dict] = mapped_column(JSON, default=dict)

    project: Mapped[Project] = relationship(back_populates="batches")
    jobs: Mapped[list[Job]] = relationship(
        back_populates="batch", cascade="all, delete-orphan"
    )
