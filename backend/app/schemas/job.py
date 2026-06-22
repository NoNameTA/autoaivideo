from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobStatus
from app.schemas.step import StepOut


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: str
    seq: int
    status: JobStatus
    pipeline: str
    vars: dict
    progress: int
    error: str | None
    created_at: datetime
    updated_at: datetime


class JobDetail(JobOut):
    steps: list[StepOut] = []
