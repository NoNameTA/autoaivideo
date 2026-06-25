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
    duplicate_count: int = 0
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
    sheet_row: int | None = None
    video_id: str | None = None
    job_id: str | None
    # Output Path (video trên máy Windows sau khi tải/Export) — KHÔNG upload, KHÔNG URL.
    output_path: str | None = None
    output_folder: str | None = None
    output_filename: str | None = None
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
    sheet_row: int | None = None


class SheetReadRequest(BaseModel):
    """Tham số đọc/import Sheet: filter (Backend lọc) + limit (Batch Import)."""

    filter: str = "all"  # all | unprocessed | failed | not_downloaded
    limit: int | None = None  # None = toàn bộ; 100/500/1000/5000…


class SheetCountResult(BaseModel):
    """Đếm TRƯỚC khi import (hiển thị tổng số sẽ import)."""

    total_rows: int
    matched: int
    new: int
    duplicate: int


class SheetImportResult(BaseModel):
    """Kết quả import từ Sheet (kèm dedup)."""

    source: VideoSourceOut
    imported: int
    duplicates: int
    matched: int


class VariationRequest(BaseModel):
    """Tạo N biến thể từ 1 video đã tải. spin/ratio tự động; caption/watermark/music tuỳ chọn."""

    count: int = 3
    spin: bool = True
    ratio: bool = False  # bật = dùng cả 3 tỉ lệ nếu không chỉ định ratios
    ratios: list[str] = []  # ví dụ ["9:16","1:1","16:9"]
    caption: bool = False  # bật = dùng title làm caption
    caption_text: str | None = None
    watermark_path: str | None = None  # đường dẫn ảnh logo (tuỳ chọn)
    music_path: str | None = None  # đường dẫn nhạc nền (tuỳ chọn)


class VariationResult(BaseModel):
    batch_id: str
    count: int


class BvsEditRequest(BaseModel):
    """Chỉnh video bằng Bulk Video Studio (qua agent BulkAuto :8787)."""

    bulkauto_url: str | None = None  # mặc định http://127.0.0.1:8787
    bvs_config: dict | None = None  # cấu hình BVS tuỳ chọn (logo/intro/outro/nhạc/speed/phụ đề)


class BvsEditResult(BaseModel):
    batch_id: str
