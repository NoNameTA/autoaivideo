from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import DEFAULT_STEP_PRIORITY
from app.db.base import Base, utcnow
from app.db.ids import new_id
from app.models.enums import QueueState


class JobQueue(Base):
    __tablename__ = "job_queue"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("q"))
    step_id: Mapped[str] = mapped_column(ForeignKey("steps.id", ondelete="CASCADE"), index=True)
    priority: Mapped[int] = mapped_column(Integer, default=DEFAULT_STEP_PRIORITY)
    state: Mapped[QueueState] = mapped_column(String(20), default=QueueState.pending, index=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    enqueued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
