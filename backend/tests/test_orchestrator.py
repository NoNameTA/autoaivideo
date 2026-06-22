"""Test orchestrator: hàng đợi bền, retry, máy trạng thái advance (SPEC 04 §4, 15 §2)."""

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.models.batch import Batch
from app.models.job import Job
from app.models.step import Step
from app.orchestrator import queue
from app.orchestrator.engine import engine
from app.orchestrator.retry import backoff_seconds, should_retry
from app.schemas.batch import BatchCreate
from app.schemas.project import ProjectCreate
from app.services.batch_service import BatchService
from app.services.project_service import ProjectService
from tests.conftest import _Session


def test_retry_policy() -> None:
    assert should_retry(True, 0, 3) is True
    assert should_retry(True, 3, 3) is False
    assert should_retry(False, 0, 3) is False
    assert backoff_seconds(0, 2) == 2
    assert backoff_seconds(2, 2) == 8


async def _make_demo_job() -> tuple[str, list[str]]:
    async with _Session() as s:
        project = await ProjectService.create(
            s, ProjectCreate(name="P", default_pipeline="local_demo")
        )
        batch = await BatchService.create(s, project.id, BatchCreate(name="B", inputs=[{"k": 1}]))
    async with _Session() as s:
        job = (await s.execute(select(Job).where(Job.batch_id == batch.id))).scalar_one()
        steps = sorted(
            (await s.execute(select(Step).where(Step.job_id == job.id))).scalars().all(),
            key=lambda x: x.order,
        )
    return job.id, [st.id for st in steps]


def test_create_enqueues_first_step() -> None:
    async def scenario() -> None:
        _, step_ids = await _make_demo_job()
        async with _Session() as s:
            pending = await queue.due_pending(s, 10)
            assert any(q.step_id == step_ids[0] for q in pending)
            assert not any(q.step_id == step_ids[1] for q in pending)

    asyncio.run(scenario())


def test_completion_advances_and_completes_job() -> None:
    async def scenario() -> None:
        job_id, step_ids = await _make_demo_job()

        # Hoàn tất step 0 -> step 1 được đưa vào hàng đợi
        await engine.on_completed(step_ids[0], [])
        async with _Session() as s:
            pending = await queue.due_pending(s, 10)
            assert any(q.step_id == step_ids[1] for q in pending)
            job = await s.get(Job, job_id)
            assert job.status == "running"

        # Hoàn tất step 1 -> job + batch completed
        await engine.on_completed(step_ids[1], [])
        async with _Session() as s:
            job = await s.get(Job, job_id)
            assert job.status == "completed"
            assert job.progress == 100
            batch = await s.get(Batch, job.batch_id)
            assert batch.status == "completed"

    asyncio.run(scenario())


def test_completion_persists_assets() -> None:
    async def scenario() -> None:
        _, step_ids = await _make_demo_job()
        await engine.on_completed(
            step_ids[0],
            [{"kind": "other", "path": "jobs/x/out.txt", "size": 3, "checksum": "abc"}],
        )
        from app.models.asset import Asset

        async with _Session() as s:
            assets = (
                await s.execute(select(Asset).where(Asset.step_id == step_ids[0]))
            ).scalars().all()
            assert len(assets) == 1
            assert assets[0].path == "jobs/x/out.txt"

    asyncio.run(scenario())


def test_non_retryable_failure_fails_job() -> None:
    async def scenario() -> None:
        job_id, step_ids = await _make_demo_job()
        await engine.on_failed(step_ids[0], "boom", retryable=False)
        async with _Session() as s:
            job = await s.get(Job, job_id)
            assert job.status == "failed"
            step = await s.get(Step, step_ids[0])
            assert step.status == "failed"

    asyncio.run(scenario())


def test_retryable_failure_requeues() -> None:
    async def scenario() -> None:
        _, step_ids = await _make_demo_job()
        await engine.on_failed(step_ids[0], "transient", retryable=True)
        async with _Session() as s:
            step = await s.get(Step, step_ids[0])
            assert step.status == "retrying"
            assert step.attempt == 1
            rows = (
                await s.execute(
                    select(queue.JobQueue).where(
                        queue.JobQueue.step_id == step_ids[0], queue.JobQueue.state == "pending"
                    )
                )
            ).scalars().all()
            assert len(rows) >= 1

    asyncio.run(scenario())
