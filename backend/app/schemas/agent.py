from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AgentStatus


class AgentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    version: str
    capabilities: list
    capacity: int
    status: AgentStatus
    os: str
    last_heartbeat: datetime | None
    registered_at: datetime
