from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BatchStatus


class BatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    # Mỗi phần tử = biến cho 1 job (vd {"topic": "...", "prompt": "..."}) (SPEC 01 §6).
    inputs: list[dict] = Field(min_length=1)
    pipeline: str | None = None


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    name: str
    status: BatchStatus
    input_count: int
    counts: dict
    created_at: datetime
    updated_at: datetime
