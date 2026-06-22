from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, status

from app.api.deps import PageDep, SessionDep, require_owner
from app.models.enums import JobStatus
from app.schemas.batch import BatchCreate, BatchOut
from app.schemas.common import Page
from app.schemas.job import JobOut
from app.services.batch_service import BatchService

router = APIRouter(prefix="/api/v1", tags=["batches"], dependencies=[Depends(require_owner)])


@router.post(
    "/projects/{project_id}/batches",
    response_model=BatchOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_batch(
    project_id: str,
    data: BatchCreate,
    session: SessionDep,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> BatchOut:
    return await BatchService.create(session, project_id, data, idempotency_key)  # type: ignore[return-value]


@router.get("/batches/{batch_id}", response_model=BatchOut)
async def get_batch(batch_id: str, session: SessionDep) -> BatchOut:
    return await BatchService.get(session, batch_id)  # type: ignore[return-value]


@router.get("/batches/{batch_id}/jobs", response_model=Page[JobOut])
async def list_batch_jobs(
    batch_id: str,
    session: SessionDep,
    page: PageDep,
    status: JobStatus | None = None,
) -> Page[JobOut]:
    limit, cursor = page
    items, next_cursor = await BatchService.list_jobs(session, batch_id, limit, cursor, status)
    return Page[JobOut](items=items, next_cursor=next_cursor)  # type: ignore[arg-type]
