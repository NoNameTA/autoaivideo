from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LogOut(BaseModel):
    """1 dòng audit-log cho trang Logs (SPEC 04 §7, 10 §2)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    level: str
    category: str = Field(validation_alias="entity_type")
    entity_id: str
    type: str
    trace_id: str | None
    data: dict
    created_at: datetime
