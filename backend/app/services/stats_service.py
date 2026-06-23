"""Thống kê vận hành từ DATA THẬT (SPEC 02 §7): job theo status, throughput,
tỉ lệ lỗi, thời gian từng adapter. Không dữ liệu giả.

Tổng hợp ở tầng Python (quy mô local) để portable SQLite↔PG, tránh hàm dialect.
"""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.enums import JobStatus, StepStatus
from app.models.job import Job
from app.models.step import Step

# Số ngày gần nhất hiển thị throughput (job hoàn tất / ngày).
THROUGHPUT_DAYS = 14


class StatsService:
    @staticmethod
    async def compute(session: AsyncSession) -> dict:
        jobs_by_status, throughput, jobs_total = await StatsService._jobs(session)
        steps_by_status, adapters, steps_total = await StatsService._steps(session)

        completed = jobs_by_status.get(JobStatus.completed.value, 0)
        failed = jobs_by_status.get(JobStatus.failed.value, 0)
        finished = completed + failed
        fail_rate = round(failed / finished, 4) if finished else 0.0

        return {
            "jobs_total": jobs_total,
            "jobs_by_status": jobs_by_status,
            "steps_total": steps_total,
            "steps_by_status": steps_by_status,
            "completed_total": completed,
            "failed_total": failed,
            "fail_rate": fail_rate,
            "throughput": throughput,
            "adapters": adapters,
            "generated_at": utcnow(),
        }

    @staticmethod
    async def _jobs(session: AsyncSession) -> tuple[dict[str, int], list[dict], int]:
        rows = (await session.execute(select(Job.status, Job.updated_at))).all()
        by_status = {s.value: 0 for s in JobStatus}

        # Khung ngày liên tục (cũ -> mới), điền 0 cho ngày không có job.
        today = utcnow().date()
        days = [today - timedelta(days=i) for i in range(THROUGHPUT_DAYS - 1, -1, -1)]
        bucket = {d.isoformat(): 0 for d in days}

        for status, updated_at in rows:
            key = str(status)
            by_status[key] = by_status.get(key, 0) + 1
            if key == JobStatus.completed.value and updated_at is not None:
                day = updated_at.date().isoformat()
                if day in bucket:
                    bucket[day] += 1

        throughput = [{"date": d, "count": c} for d, c in bucket.items()]
        return by_status, throughput, len(rows)

    @staticmethod
    async def _steps(session: AsyncSession) -> tuple[dict[str, int], list[dict], int]:
        rows = (
            await session.execute(
                select(Step.adapter, Step.status, Step.started_at, Step.finished_at)
            )
        ).all()
        by_status = {s.value: 0 for s in StepStatus}
        agg: dict[str, dict] = {}

        for adapter, status, started_at, finished_at in rows:
            key = str(status)
            by_status[key] = by_status.get(key, 0) + 1
            a = agg.setdefault(adapter, {"count": 0, "failed": 0, "total_sec": 0.0, "timed": 0})
            a["count"] += 1
            if key == StepStatus.failed.value:
                a["failed"] += 1
            if started_at is not None and finished_at is not None:
                a["total_sec"] += max((finished_at - started_at).total_seconds(), 0.0)
                a["timed"] += 1

        adapters = [
            {
                "adapter": name,
                "count": a["count"],
                "failed": a["failed"],
                "avg_seconds": round(a["total_sec"] / a["timed"], 2) if a["timed"] else 0.0,
            }
            for name, a in sorted(agg.items(), key=lambda kv: kv[1]["count"], reverse=True)
        ]
        return by_status, adapters, len(rows)
