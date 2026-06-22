"""Integration: timeout requeue + resume-on-restart (SPEC 04 §4/§8)."""

from __future__ import annotations

import asyncio
from datetime import timedelta

from sqlalchemy import select

from app.db.base import utcnow
from app.models.agent import Agent
from app.models.enums import AgentStatus, StepStatus
from app.models.job_queue import JobQueue
from app.models.step import Step
from app.orchestrator.engine import engine
from app.schemas.batch import BatchCreate
from app.schemas.project import ProjectCreate
from app.services.batch_service import BatchService
from app.services.project_service import ProjectService
from tests.conftest import _Session


async def _make_job_first_step() -> str:
    async with _Session() as s:
        p = await ProjectService.create(s, ProjectCreate(name="P", default_pipeline="local_demo"))
        await BatchService.create(s, p.id, BatchCreate(name="B", inputs=[{"k": 1}]))
    async with _Session() as s:
        steps = sorted(
            (await s.execute(select(Step))).scalars().all(), key=lambda x: x.order
        )
    return steps[0].id


def test_resume_requeues_running_step_and_marks_agent_offline() -> None:
    async def scenario() -> None:
        step_id = await _make_job_first_step()
        async with _Session() as s:
            st = await s.get(Step, step_id)
            st.status = StepStatus.running
            st.assigned_agent = "ag1"
            s.add(Agent(id="ag1", status=AgentStatus.online))
            for row in (
                await s.execute(select(JobQueue).where(JobQueue.step_id == step_id))
            ).scalars().all():
                row.state = "leased"
            await s.commit()

        await engine.resume()

        async with _Session() as s:
            st = await s.get(Step, step_id)
            assert st.status == StepStatus.queued
            assert st.assigned_agent is None
            ag = await s.get(Agent, "ag1")
            assert ag.status == AgentStatus.offline
            pending = (
                await s.execute(
                    select(JobQueue).where(
                        JobQueue.step_id == step_id, JobQueue.state == "pending"
                    )
                )
            ).scalars().all()
            assert pending

    asyncio.run(scenario())


def test_ack_timeout_requeues_step() -> None:
    async def scenario() -> None:
        step_id = await _make_job_first_step()
        async with _Session() as s:
            st = await s.get(Step, step_id)
            st.status = StepStatus.assigned
            st.assigned_agent = "ag1"
            for row in (
                await s.execute(select(JobQueue).where(JobQueue.step_id == step_id))
            ).scalars().all():
                row.state = "leased"
                row.lease_until = utcnow() - timedelta(seconds=1)
            await s.commit()

        async with _Session() as s:
            await engine._handle_timeouts(s)

        async with _Session() as s:
            st = await s.get(Step, step_id)
            assert st.status == StepStatus.queued
            pending = (
                await s.execute(
                    select(JobQueue).where(
                        JobQueue.step_id == step_id, JobQueue.state == "pending"
                    )
                )
            ).scalars().all()
            assert pending

    asyncio.run(scenario())
