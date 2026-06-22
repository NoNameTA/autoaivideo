from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_owner
from app.schemas.job import JobDetail, JobOut
from app.services.job_service import JobService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"], dependencies=[Depends(require_owner)])


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str, session: SessionDep) -> JobDetail:
    return await JobService.get_detail(session, job_id)  # type: ignore[return-value]


@router.post("/{job_id}/retry", response_model=JobOut)
async def retry_job(job_id: str, session: SessionDep) -> JobOut:
    return await JobService.retry(session, job_id)  # type: ignore[return-value]


@router.post("/{job_id}/cancel", response_model=JobOut)
async def cancel_job(job_id: str, session: SessionDep) -> JobOut:
    return await JobService.cancel(session, job_id)  # type: ignore[return-value]
