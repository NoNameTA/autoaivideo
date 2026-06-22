from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PluginRegister(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    version: str = ""
    capability: str = ""
    type: str = ""
    manifest: dict = Field(default_factory=dict)
    config: dict = Field(default_factory=dict)


class PluginUpdate(BaseModel):
    enabled: bool | None = None
    config: dict | None = None


class PluginOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str
    capability: str
    type: str
    enabled: bool
    config: dict
    manifest: dict
    installed_at: datetime


class PluginSchema(BaseModel):
    """Trả JSON Schema cấu hình plugin (SPEC 04 §2, 08 §7)."""

    name: str
    schema_: dict = Field(serialization_alias="schema")
