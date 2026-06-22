"""Hàng đợi bền (durable) — thao tác trên bảng job_queue (SPEC 04 §4, 10)."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import DEFAULT_STEP_PRIORITY
from app.db.base import utcnow
from app.models.enums import StepStatus
from app.models.job_queue import JobQueue
from app.models.step import Step


async def enqueue(
    session: AsyncSession,
    step_id: str,
    *,
    priority: int = DEFAULT_STEP_PRIORITY,
    delay_seconds: int = 0,
) -> JobQueue:
    row = JobQueue(
        step_id=step_id,
        priority=priority,
        state="pending",
        enqueued_at=utcnow() + timedelta(seconds=delay_seconds),
    )
    session.add(row)
    return row


async def due_pending(session: AsyncSession, limit: int) -> list[JobQueue]:
    if limit <= 0:
        return []
    stmt = (
        select(JobQueue)
        .where(JobQueue.state == "pending", JobQueue.enqueued_at <= utcnow())
        .order_by(JobQueue.priority, JobQueue.enqueued_at)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def leased_expired(session: AsyncSession) -> list[JobQueue]:
    stmt = select(JobQueue).where(
        JobQueue.state == "leased",
        JobQueue.lease_until.is_not(None),
        JobQueue.lease_until < utcnow(),
    )
    return list((await session.execute(stmt)).scalars().all())


async def mark_done(session: AsyncSession, step_id: str) -> None:
    stmt = select(JobQueue).where(JobQueue.step_id == step_id, JobQueue.state != "done")
    for row in (await session.execute(stmt)).scalars().all():
        row.state = "done"


async def active_step_count(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(Step).where(
        Step.status.in_([StepStatus.assigned, StepStatus.running])
    )
    return int((await session.execute(stmt)).scalar_one())
