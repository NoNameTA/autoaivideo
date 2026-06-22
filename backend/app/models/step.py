from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DEFAULT_MAX_RETRIES
from app.db.base import Base, TimestampMixin
from app.db.ids import new_id
from app.models.enums import StepStatus

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.job import Job


class Step(Base, TimestampMixin):
    __tablename__ = "steps"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("step"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    step_key: Mapped[str] = mapped_column(String(100))
    order: Mapped[int] = mapped_column(Integer, default=0)
    adapter: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[StepStatus] = mapped_column(String(20), default=StepStatus.queued, index=True)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=DEFAULT_MAX_RETRIES)
    assigned_agent: Mapped[str | None] = mapped_column(
        ForeignKey("agents.id", ondelete="SET NULL"), default=None
    )
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    idempotency_key: Mapped[str] = mapped_column(
        String(120), unique=True, default=lambda: new_id("idem")
    )

    job: Mapped[Job] = relationship(back_populates="steps")
    assets: Mapped[list[Asset]] = relationship(
        back_populates="step", cascade="all, delete-orphan"
    )
