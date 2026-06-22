from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError
from app.models.enums import JobStatus, StepStatus
from app.models.job import Job


class JobService:
    @staticmethod
    async def get_detail(session: AsyncSession, job_id: str) -> Job:
        stmt = select(Job).where(Job.id == job_id).options(selectinload(Job.steps))
        job = (await session.execute(stmt)).scalar_one_or_none()
        if not job:
            raise NotFoundError(f"Job '{job_id}' không tồn tại")
        return job

    @staticmethod
    async def retry(session: AsyncSession, job_id: str) -> Job:
        job = await JobService.get_detail(session, job_id)
        if job.status not in (JobStatus.failed, JobStatus.cancelled):
            raise ConflictError("Chỉ retry được job đang failed hoặc cancelled")
        for step in job.steps:
            if step.status in (StepStatus.failed, StepStatus.cancelled):
                step.status = StepStatus.queued
                step.error = None
        job.status = JobStatus.queued
        job.error = None
        await session.commit()
        await session.refresh(job)
        return job

    @staticmethod
    async def cancel(session: AsyncSession, job_id: str) -> Job:
        job = await JobService.get_detail(session, job_id)
        if job.status in (JobStatus.completed, JobStatus.cancelled):
            raise ConflictError("Job đã kết thúc, không thể huỷ")
        for step in job.steps:
            if step.status not in (StepStatus.completed,):
                step.status = StepStatus.cancelled
        job.status = JobStatus.cancelled
        await session.commit()
        await session.refresh(job)
        return job
