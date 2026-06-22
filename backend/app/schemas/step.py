from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import StepStatus


class StepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    step_key: str
    order: int
    adapter: str
    status: StepStatus
    attempt: int
    max_retries: int
    assigned_agent: str | None
    inputs: dict
    config: dict
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None
