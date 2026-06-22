from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.ids import new_id
from app.models.enums import JobStatus

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.batch import Batch
    from app.models.step import Step


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("job"))
    batch_id: Mapped[str] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), index=True
    )
    seq: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[JobStatus] = mapped_column(String(20), default=JobStatus.queued, index=True)
    pipeline: Mapped[str] = mapped_column(String(100))
    vars: Mapped[dict] = mapped_column(JSON, default=dict)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, default=None)

    batch: Mapped[Batch] = relationship(back_populates="jobs")
    steps: Mapped[list[Step]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="Step.order"
    )
    assets: Mapped[list[Asset]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )
