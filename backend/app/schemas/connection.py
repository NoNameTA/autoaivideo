from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConnectionCreate(BaseModel):
    provider: str = Field(min_length=1, max_length=60)
    credential_id: str | None = None
    display_name: str = Field(min_length=1, max_length=160)
    capabilities: list[str] = []
    settings: dict = {}


class ConnectionUpdate(BaseModel):
    credential_id: str | None = None
    display_name: str | None = None
    enabled: bool | None = None
    capabilities: list[str] | None = None
    settings: dict | None = None


class ConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    credential_id: str | None
    display_name: str
    enabled: bool
    health_status: str
    last_check: datetime | None
    capabilities: list
    settings: dict
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None


class ConnectionTestResult(BaseModel):
    ok: bool
    health_status: str
    message: str
