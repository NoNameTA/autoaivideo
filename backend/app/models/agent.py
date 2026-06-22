from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.models.enums import AgentStatus


class Agent(Base):
    __tablename__ = "agents"

    # agent_id do agent tự khai (SPEC 05 §3), không sinh tự động.
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    version: Mapped[str] = mapped_column(String(40), default="")
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[AgentStatus] = mapped_column(String(20), default=AgentStatus.offline)
    os: Mapped[str] = mapped_column(String(40), default="")
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
