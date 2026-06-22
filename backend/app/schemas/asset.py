from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AssetKind


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    step_id: str
    job_id: str
    kind: AssetKind
    path: str
    mime: str | None
    size: int
    checksum: str | None
    created_at: datetime
