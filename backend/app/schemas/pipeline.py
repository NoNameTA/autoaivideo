from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StepDef(BaseModel):
    step_key: str = Field(min_length=1, max_length=100)
    adapter: str = Field(min_length=1, max_length=100)
    config: dict = Field(default_factory=dict)


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, pattern=r"^[A-Za-z0-9_-]+$")
    description: str = ""
    steps: list[StepDef] = Field(min_length=1)


class PipelineUpdate(BaseModel):
    description: str | None = None
    steps: list[StepDef] | None = None


class PipelineRunBody(BaseModel):
    project_id: str = Field(min_length=1)
    name: str = Field(default="Run", min_length=1, max_length=200)
    inputs: list[dict] = Field(min_length=1)


class PipelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    steps: list[StepDef]
    builtin: bool
    created_at: datetime
    updated_at: datetime
