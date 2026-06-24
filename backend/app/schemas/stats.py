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
    generated_at: datetime
