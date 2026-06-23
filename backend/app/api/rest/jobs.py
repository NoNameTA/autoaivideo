from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, require_owner
from app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from app.models.enums import JobStatus
from app.schemas.job import JobDetail, JobOut
from app.services.job_service import JobService

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"], dependencies=[Depends(require_owner)])


@router.get("", response_model=list[JobOut])
async def list_jobs(
    session: SessionDep,
    status: JobStatus | None = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
) -> list[JobOut]:
    return await JobService.list_all(session, limit, status, search)  # type: ignore[return-value]


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: str, session: SessionDep) -> JobDetail:
    return await JobService.get_detail(session, job_id)  # type: ignore[return-value]


@router.post("/{job_id}/retry", response_model=JobOut)
async def retry_job(job_id: str, session: SessionDep) -> JobOut:
    return await JobService.retry(session, job_id)  # type: ignore[return-value]


@router.post("/{job_id}/cancel", response_model=JobOut)
async def cancel_job(job_id: str, session: SessionDep) -> JobOut:
    return await JobService.cancel(session, job_id)  # type: ignore[return-value]
