from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VideoSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_type: str = "direct_url"
    config: dict = {}


class VideoSourceUpdate(BaseModel):
    name: str | None = None
    config: dict | None = None


class VideoSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source_type: str
    config: dict
    status: str
    item_count: int
    created_at: datetime
    updated_at: datetime


class VideoSourceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    seq: int
    url: str
    title: str | None
    status: str
    job_id: str | None
    created_at: datetime
    updated_at: datetime


class AddLinks(BaseModel):
    """Thêm/nhập nhiều link (Direct URL). `urls` đã tách dòng phía client hoặc text thô."""

    urls: list[str] = []
    # Văn bản thô (paste nhiều dòng / nội dung file txt-csv) — backend tự tách & lấy URL.
    text: str | None = None


class RunRequest(BaseModel):
    item_ids: list[str] | None = None  # None = tất cả pending
    project_id: str | None = None  # None = project mặc định "Video Sources"
    pipeline: str = "video_download"


class RunResult(BaseModel):
    batch_id: str
    job_count: int


class SheetPreviewRow(BaseModel):
    """1 dòng preview đọc từ Google Sheet (CHƯA import, chưa tạo job)."""

    seq: int
    url: str
    title: str | None
    status: str
