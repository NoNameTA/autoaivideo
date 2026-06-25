from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ThroughputPoint(BaseModel):
    date: str
    count: int


class AdapterStat(BaseModel):
    adapter: str
    count: int
    failed: int
    avg_seconds: float


class VideoStats(BaseModel):
    sources_total: int
    items_total: int
    items_by_status: dict[str, int]
    total_asset_bytes: int


class DownloadStats(BaseModel):
    """Metric tải video (media.download / yt-dlp)."""

    downloads_total: int
    downloads_success: int
    downloads_failed: int
    total_bytes: int
    download_seconds: float
    avg_speed_bps: float


class EditStats(BaseModel):
    """Metric chỉnh sửa + Export (video.ffmpeg / video.bulkauto) — KHÔNG upload."""

    edits_total: int
    edits_success: int
    edits_failed: int
    exported_total: int
    export_bytes: int
    edit_seconds: float
    avg_edit_seconds: float


class CookieStats(BaseModel):
    """Metric Cookie Manager (status-only)."""

    configured: int
    loaded: int
    valid: int
    expired: int
    downloads_with_cookie: int
    downloads_without_cookie: int
    downloads_by_platform: dict[str, int] = {}


class StatsOut(BaseModel):
    """Thống kê vận hành (SPEC 02 §7)."""

    jobs_total: int
    jobs_by_status: dict[str, int]
    steps_total: int
    steps_by_status: dict[str, int]
    completed_total: int
    failed_total: int
    fail_rate: float
    throughput: list[ThroughputPoint]
    adapters: list[AdapterStat]
    video: VideoStats
    download: DownloadStats
    edit: EditStats
    cookies: CookieStats
    generated_at: datetime
