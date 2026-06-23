"""Test trang Statistics: thống kê từ data thật jobs/steps (SPEC 02 §7)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from fastapi.testclient import TestClient

from app.db.base import utcnow
from app.models.batch import Batch
from app.models.enums import JobStatus, StepStatus
from app.models.job import Job
from app.models.project import Project
from app.models.step import Step
from tests.conftest import OWNER_HEADERS, _Session


def test_stats_empty(client: TestClient) -> None:
    r = client.get("/api/v1/stats", headers=OWNER_HEADERS)
    assert r.status_code == 200
    data = r.json()
    assert data["jobs_total"] == 0
    assert data["steps_total"] == 0
    assert data["fail_rate"] == 0.0
    assert data["adapters"] == []
    # throughput luôn có đủ khung 14 ngày, tất cả 0.
    assert len(data["throughput"]) == 14
    assert all(p["count"] == 0 for p in data["throughput"])


async def _seed() -> None:
    t0 = utcnow()
    async with _Session() as s:
        proj = Project(name="P")
        s.add(proj)
        await s.flush()
        batch = Batch(project_id=proj.id, name="B", input_count=2)
        s.add(batch)
        await s.flush()
        job_ok = Job(batch_id=batch.id, seq=0, status=JobStatus.completed, pipeline="p")
        job_bad = Job(batch_id=batch.id, seq=1, status=JobStatus.failed, pipeline="p")
        s.add_all([job_ok, job_bad])
        await s.flush()
        s.add_all(
            [
                Step(
                    job_id=job_ok.id, step_key="a", order=0, adapter="video.ffmpeg",
                    status=StepStatus.completed,
                    started_at=t0, finished_at=t0 + timedelta(seconds=10),
                ),
                Step(
                    job_id=job_ok.id, step_key="b", order=1, adapter="web.cdp",
                    status=StepStatus.completed,
                    started_at=t0, finished_at=t0 + timedelta(seconds=4),
                ),
                Step(
                    job_id=job_bad.id, step_key="a", order=0, adapter="video.ffmpeg",
                    status=StepStatus.failed,
                    started_at=t0, finished_at=t0 + timedelta(seconds=6),
                ),
            ]
        )
        await s.commit()


def test_stats_with_data(client: TestClient) -> None:
    asyncio.run(_seed())
    data = client.get("/api/v1/stats", headers=OWNER_HEADERS).json()

    assert data["jobs_total"] == 2
    assert data["jobs_by_status"]["completed"] == 1
    assert data["jobs_by_status"]["failed"] == 1
    assert data["completed_total"] == 1
    assert data["failed_total"] == 1
    assert data["fail_rate"] == 0.5  # 1 failed / (1 completed + 1 failed)

    assert data["steps_total"] == 3
    assert data["steps_by_status"]["completed"] == 2
    assert data["steps_by_status"]["failed"] == 1

    adapters = {a["adapter"]: a for a in data["adapters"]}
    assert adapters["video.ffmpeg"]["count"] == 2
    assert adapters["video.ffmpeg"]["failed"] == 1
    assert adapters["video.ffmpeg"]["avg_seconds"] == 8.0  # (10 + 6) / 2
    assert adapters["web.cdp"]["count"] == 1
    assert adapters["web.cdp"]["avg_seconds"] == 4.0
    # adapter nhiều step nhất đứng trước.
    assert data["adapters"][0]["adapter"] == "video.ffmpeg"

    # Job completed hôm nay -> throughput ngày cuối khung = 1.
    assert data["throughput"][-1]["count"] == 1
