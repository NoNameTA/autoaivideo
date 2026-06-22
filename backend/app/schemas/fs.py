from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AllowedFolderCreate(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    label: str = ""


class AllowedFolderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    path: str
    label: str
    created_at: datetime


class PathBody(BaseModel):
    path: str = Field(min_length=1)


class CopyMoveBody(BaseModel):
    src: str = Field(min_length=1)
    dst: str = Field(min_length=1)


class RenameBody(BaseModel):
    path: str = Field(min_length=1)
    new_name: str = Field(min_length=1, max_length=255)


class ReadBody(BaseModel):
    path: str = Field(min_length=1)
    max_bytes: int = Field(default=1_048_576, ge=1, le=10_485_760)


class WatchBody(BaseModel):
    path: str = Field(min_length=1)
    enable: bool = True
