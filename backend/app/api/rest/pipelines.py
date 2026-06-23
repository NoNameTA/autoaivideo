from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.batch import BatchCreate, BatchOut
from app.schemas.pipeline import (
    PipelineCreate,
    PipelineOut,
    PipelineRunBody,
    PipelineUpdate,
)
from app.services.batch_service import BatchService
from app.services.pipeline_service import PipelineService

router = APIRouter(
    prefix="/api/v1/pipelines", tags=["pipelines"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[PipelineOut])
async def list_pipelines(session: SessionDep) -> list[PipelineOut]:
    return await PipelineService.list(session)  # type: ignore[return-value]


@router.post("", response_model=PipelineOut, status_code=status.HTTP_201_CREATED)
async def create_pipeline(data: PipelineCreate, session: SessionDep) -> PipelineOut:
    return await PipelineService.create(session, data)  # type: ignore[return-value]


@router.get("/{name}", response_model=PipelineOut)
async def get_pipeline(name: str, session: SessionDep) -> PipelineOut:
    return await PipelineService.get(session, name)  # type: ignore[return-value]


@router.patch("/{name}", response_model=PipelineOut)
async def update_pipeline(name: str, data: PipelineUpdate, session: SessionDep) -> PipelineOut:
    return await PipelineService.update(session, name, data)  # type: ignore[return-value]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pipeline(name: str, session: SessionDep):
    await PipelineService.delete(session, name)


@router.post("/{name}/run", response_model=BatchOut, status_code=status.HTTP_201_CREATED)
async def run_pipeline(name: str, body: PipelineRunBody, session: SessionDep) -> BatchOut:
    # Chạy workflow = tạo batch với pipeline này (SPEC 02 §4).
    await PipelineService.get(session, name)
    data = BatchCreate(name=body.name, inputs=body.inputs, pipeline=name)
    return await BatchService.create(session, body.project_id, data)  # type: ignore[return-value]
