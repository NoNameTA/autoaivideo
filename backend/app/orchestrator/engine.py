"""Orchestrator engine (SPEC 02 §3, 04 §4): durable queue + dispatcher + state machine
+ retry/backoff + ack/heartbeat timeout + resume-on-startup.

Engine chạy như background asyncio task trong tiến trình FastAPI. Dispatch gửi step.assign
tới agent qua AgentRegistry; kết quả về qua /ws/agent gọi các handler on_*.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.ws.manager import manager
from app.core.config import get_settings
from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models.agent import Agent
from app.models.asset import Asset
from app.models.enums import AgentStatus, BatchStatus, JobStatus, StepStatus
from app.models.job import Job
from app.models.job_queue import JobQueue
from app.models.step import Step
from app.orchestrator import queue
from app.orchestrator.agent_registry import registry
from app.orchestrator.dispatcher import build_assign
from app.orchestrator.retry import backoff_seconds, should_retry
from app.plugins.registry_cache import is_plugin_capability
from app.services.event_service import EventService

log = logging.getLogger("orchestrator")

_TERMINAL_JOB = {JobStatus.completed, JobStatus.failed, JobStatus.cancelled}


class OrchestratorEngine:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._running = False

    # ----- vòng đời -----
    async def start(self) -> None:
        await self.resume()
        self._running = True
        self._task = asyncio.create_task(self._loop())
        log.info("Orchestrator engine started")

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        interval = get_settings().engine_tick_seconds
        while self._running:
            try:
                await self.tick()
            except Exception:  # noqa: BLE001 - không để loop chết
                log.exception("engine tick lỗi")
            await asyncio.sleep(interval)

    # ----- khôi phục sau restart (SPEC 04 §8) -----
    async def resume(self) -> None:
        async with SessionLocal() as session:
            await session.execute(
                update(Step)
                .where(Step.status.in_([StepStatus.assigned, StepStatus.running]))
                .values(status=StepStatus.queued, assigned_agent=None)
            )
            await session.execute(
                update(JobQueue)
                .where(JobQueue.state == "leased")
                .values(state="pending", lease_until=None)
            )
            await session.execute(
                update(Agent).where(Agent.status != AgentStatus.offline).values(
                    status=AgentStatus.offline
                )
            )
            await session.commit()

    # ----- tick: timeout + dispatch -----
    async def tick(self) -> None:
        s = get_settings()
        async with SessionLocal() as session:
            await self._handle_timeouts(session)

            budget = s.max_concurrent_steps - await queue.active_step_count(session)
            rows = await queue.due_pending(session, budget)
            for q in rows:
                step = await session.get(Step, q.step_id)
                if step is None or step.status not in (StepStatus.queued, StepStatus.retrying):
                    q.state = "done"
                    await session.commit()
                    continue
                conn = registry.pick(step.adapter)
                if conn is None:
                    continue  # không có agent phù hợp -> để pending (SPEC 04 §4)
                job = await session.get(Job, step.job_id)
                q.state = "leased"
                q.lease_until = utcnow() + timedelta(seconds=s.ack_timeout)
                step.status = StepStatus.assigned
                step.assigned_agent = conn.agent_id
                if job:
                    job.status = JobStatus.running
                conn.inflight += 1
                await session.commit()

                ok = await registry.send(
                    conn.agent_id, build_assign(step, job, s.heartbeat_timeout)
                )
                if not ok:
                    registry.dec_inflight(conn.agent_id)
                    q.state = "pending"
                    q.lease_until = None
                    q.enqueued_at = utcnow()
                    step.status = (
                        StepStatus.retrying if step.attempt > 0 else StepStatus.queued
                    )
                    step.assigned_agent = None
                    await session.commit()
                elif job:
                    await self._broadcast_step(step, job)

    async def _handle_timeouts(self, session: AsyncSession) -> None:
        for q in await queue.leased_expired(session):
            step = await session.get(Step, q.step_id)
            if step is None:
                q.state = "done"
                continue
            if step.assigned_agent:
                registry.dec_inflight(step.assigned_agent)
            if step.status == StepStatus.assigned:
                # ack timeout -> requeue
                step.status = StepStatus.retrying if step.attempt > 0 else StepStatus.queued
                step.assigned_agent = None
                q.state = "pending"
                q.lease_until = None
                q.enqueued_at = utcnow()
            elif step.status == StepStatus.running:
                q.state = "done"
                await self._fail_step(session, step, "Hết thời gian (heartbeat)", retryable=True)
        await session.commit()

    # ----- handler từ agent (qua /ws/agent) -----
    async def on_ack(self, step_id: str) -> None:
        s = get_settings()
        async with SessionLocal() as session:
            step = await session.get(Step, step_id)
            if step is None or step.status != StepStatus.assigned:
                return
            step.status = StepStatus.running
            step.started_at = utcnow()
            rows = (
                await session.execute(
                    select(JobQueue).where(JobQueue.step_id == step_id, JobQueue.state == "leased")
                )
            ).scalars().all()
            for row in rows:
                row.lease_until = utcnow() + timedelta(seconds=s.heartbeat_timeout)
            await session.commit()
            job = await session.get(Job, step.job_id)
            if job:
                await self._broadcast_step(step, job)
            if is_plugin_capability(step.adapter):
                await self._activity(
                    "plugin.runtime.started",
                    step_id=step.id,
                    job_id=step.job_id,
                    capability=step.adapter,
                )

    async def on_progress(
        self, step_id: str, pct: int | None, msg: str | None = None
    ) -> None:
        async with SessionLocal() as session:
            step = await session.get(Step, step_id)
            if step is None:
                return
            job = await session.get(Job, step.job_id)
            if job and pct is not None:
                # Cập nhật % của job đang chạy để Queue (jobs-all) hiển thị realtime.
                job.progress = pct
                await session.commit()
                await manager.broadcast(
                    "step.updated",
                    {
                        "job_id": job.id,
                        "step_id": step_id,
                        "status": step.status,
                        "progress": pct,
                        "msg": msg,
                    },
                    scope="batch",
                    id_=job.batch_id,
                )
                # Phát global để Queue/Dashboard refetch + hiện progress/speed/ETA.
                await manager.broadcast(
                    "job.progress", {"job_id": job.id, "progress": pct, "msg": msg}
                )
            if is_plugin_capability(step.adapter):
                await self._activity(
                    "plugin.runtime.progress", step_id=step_id, capability=step.adapter, pct=pct
                )

    async def on_completed(self, step_id: str, assets: list[dict]) -> None:
        async with SessionLocal() as session:
            step = await session.get(Step, step_id)
            if step is None:
                return
            step.status = StepStatus.completed
            step.finished_at = utcnow()
            for a in assets:
                session.add(
                    Asset(
                        step_id=step.id,
                        job_id=step.job_id,
                        kind=a.get("kind", "other"),
                        path=a.get("path", ""),
                        mime=a.get("mime"),
                        size=int(a.get("size", 0)),
                        checksum=a.get("checksum"),
                    )
                )
            if step.assigned_agent:
                registry.dec_inflight(step.assigned_agent)
            await queue.mark_done(session, step_id)
            await session.commit()
            if is_plugin_capability(step.adapter):
                await self._activity(
                    "plugin.runtime.finished",
                    step_id=step.id,
                    job_id=step.job_id,
                    capability=step.adapter,
                )
            await self._advance(session, step.job_id)

    async def on_failed(self, step_id: str, error: str, retryable: bool) -> None:
        async with SessionLocal() as session:
            step = await session.get(Step, step_id)
            if step is None:
                return
            if step.assigned_agent:
                registry.dec_inflight(step.assigned_agent)
            await self._fail_step(session, step, error, retryable=retryable)
            await session.commit()

    # ----- nội bộ -----
    async def _fail_step(
        self, session: AsyncSession, step: Step, error: str, *, retryable: bool
    ) -> None:
        base = get_settings().retry_base_seconds
        await queue.mark_done(session, step.id)
        if should_retry(retryable, step.attempt, step.max_retries):
            step.attempt += 1
            step.status = StepStatus.retrying
            step.error = error
            step.assigned_agent = None
            await queue.enqueue(
                session, step.id, delay_seconds=backoff_seconds(step.attempt, base)
            )
            await session.commit()
        else:
            step.status = StepStatus.failed
            step.error = error
            await session.commit()
            if is_plugin_capability(step.adapter):
                await self._activity(
                    "plugin.runtime.failed",
                    step_id=step.id,
                    capability=step.adapter,
                    error=error,
                )
            await self._advance(session, step.job_id)

    async def _advance(self, session: AsyncSession, job_id: str) -> None:
        job = (
            await session.execute(
                select(Job).where(Job.id == job_id).options(selectinload(Job.steps))
            )
        ).scalar_one_or_none()
        if job is None or job.status in _TERMINAL_JOB:
            return

        steps = sorted(job.steps, key=lambda x: x.order)
        total = len(steps)
        completed = [s for s in steps if s.status == StepStatus.completed]
        has_failed = any(s.status == StepStatus.failed for s in steps)
        in_progress = any(
            s.status in (StepStatus.assigned, StepStatus.running) for s in steps
        )

        if has_failed:
            job.status = JobStatus.failed
        elif len(completed) == total:
            job.status = JobStatus.completed
        else:
            job.status = JobStatus.running
            nxt = next((s for s in steps if s.status != StepStatus.completed), None)
            if (
                nxt is not None
                and nxt.status in (StepStatus.queued, StepStatus.retrying)
                and not in_progress
                and not await self._has_open_queue(session, nxt.id)
            ):
                await queue.enqueue(session, nxt.id)

        job.progress = int(len(completed) / total * 100) if total else 100
        became_terminal = job.status in _TERMINAL_JOB
        await session.commit()
        await self._update_batch(session, job.batch_id)
        await manager.broadcast(
            "job.updated",
            {"job_id": job.id, "status": job.status, "progress": job.progress},
            scope="batch",
            id_=job.batch_id,
        )
        await self._activity(
            "job.updated",
            job_id=job.id,
            batch_id=job.batch_id,
            status=job.status,
            progress=job.progress,
        )
        # Google Sheets write-back (additive, session riêng, KHÔNG làm hỏng engine nếu lỗi).
        if became_terminal:
            from app.services.sheet_writeback import on_job_terminal

            await on_job_terminal(job.id)

    async def _has_open_queue(self, session: AsyncSession, step_id: str) -> bool:
        row = (
            await session.execute(
                select(JobQueue.id).where(
                    JobQueue.step_id == step_id, JobQueue.state.in_(["pending", "leased"])
                )
            )
        ).first()
        return row is not None

    async def _update_batch(self, session: AsyncSession, batch_id: str) -> None:
        from app.models.batch import Batch  # tránh import vòng ở đầu module

        jobs = (
            await session.execute(select(Job.status).where(Job.batch_id == batch_id))
        ).scalars().all()
        counts = {st.value: 0 for st in JobStatus}
        for js in jobs:
            counts[js] = counts.get(js, 0) + 1
        batch = await session.get(Batch, batch_id)
        if batch is None:
            return
        batch.counts = counts
        if counts[JobStatus.running] or counts[JobStatus.queued]:
            batch.status = BatchStatus.running
        elif counts[JobStatus.failed]:
            batch.status = BatchStatus.failed
        elif counts[JobStatus.completed] == len(jobs) and jobs:
            batch.status = BatchStatus.completed
        await session.commit()
        await manager.broadcast(
            "batch.updated", {"batch_id": batch_id, "counts": counts}, scope="batch", id_=batch_id
        )

    async def _activity(self, kind: str, **data) -> None:
        """Ghi audit-log (DB) + phát kênh global Activity Stream (SPEC 04 §7, 09 §4.1)."""
        await EventService.from_activity(kind, data)

    async def _broadcast_step(self, step: Step, job: Job) -> None:
        await manager.broadcast(
            "step.updated",
            {
                "job_id": job.id,
                "step_id": step.id,
                "status": step.status,
                "error": step.error,
            },
            scope="batch",
            id_=job.batch_id,
        )


engine = OrchestratorEngine()
