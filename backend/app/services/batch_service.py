from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.batch import Batch
from app.models.enums import BatchStatus, JobStatus, StepStatus
from app.models.event import Event
from app.models.job import Job
from app.models.project import Project
from app.models.step import Step
from app.orchestrator import queue
from app.orchestrator.templates import get_template_steps
from app.schemas.batch import BatchCreate
from app.services.pagination import paginate

_IDEMPOTENCY_ENTITY = "idempotency_batch"


def _idem_id(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:40]


class BatchService:
    @staticmethod
    async def create(
        session: AsyncSession,
        project_id: str,
        data: BatchCreate,
        idempotency_key: str | None = None,
    ) -> Batch:
        # Idempotency (SPEC 09 §5): cùng key -> trả batch đã tạo, không tạo trùng.
        if idempotency_key:
            existing = await session.get(Event, _idem_id(idempotency_key))
            if existing is not None:
                return await BatchService.get(session, existing.data["batch_id"])

        project = await session.get(Project, project_id)
        if not project:
            raise NotFoundError(f"Project '{project_id}' không tồn tại")

        pipeline = data.pipeline or project.default_pipeline
        step_defs = get_template_steps(pipeline)  # NotFoundError nếu template sai

        # Toàn bộ trong một transaction (SPEC 10 §4).
        batch = Batch(
            project_id=project_id,
            name=data.name,
            status=BatchStatus.created,
            input_count=len(data.inputs),
            counts={
                "queued": len(data.inputs),
                "running": 0,
                "completed": 0,
                "failed": 0,
            },
        )
        session.add(batch)
        await session.flush()

        for seq, row in enumerate(data.inputs):
            job = Job(
                batch_id=batch.id,
                seq=seq,
                pipeline=pipeline,
                vars=row,
                status=JobStatus.queued,
            )
            session.add(job)
            await session.flush()
            first_step: Step | None = None
            for order, sd in enumerate(step_defs):
                step = Step(
                    job_id=job.id,
                    step_key=sd["step_key"],
                    order=order,
                    adapter=sd["adapter"],
                    inputs={**row, **sd.get("inputs", {})},
                    config=sd.get("config", {}),
                    status=StepStatus.queued,
                )
                session.add(step)
                if order == 0:
                    first_step = step
            await session.flush()
            if first_step is not None:
                # Đưa step đầu vào hàng đợi bền để engine điều phối (SPEC 04 §4).
                await queue.enqueue(session, first_step.id)

        if idempotency_key:
            session.add(
                Event(
                    id=_idem_id(idempotency_key),
                    entity_type=_IDEMPOTENCY_ENTITY,
                    entity_id=batch.id,
                    type="created",
                    data={"batch_id": batch.id},
                )
            )

        await session.commit()
        await session.refresh(batch)
        return batch

    @staticmethod
    async def get(session: AsyncSession, batch_id: str) -> Batch:
        batch = await session.get(Batch, batch_id)
        if not batch:
            raise NotFoundError(f"Batch '{batch_id}' không tồn tại")
        return batch

    @staticmethod
    async def list_jobs(
        session: AsyncSession,
        batch_id: str,
        limit: int,
        cursor: str | None,
        status: JobStatus | None,
    ) -> tuple[list[Job], str | None]:
        await BatchService.get(session, batch_id)
        stmt = select(Job).where(Job.batch_id == batch_id)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        return await paginate(session, stmt, Job.id, limit, cursor)
