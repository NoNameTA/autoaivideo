from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.video_source import (
    AddLinks,
    RunRequest,
    RunResult,
    VideoSourceCreate,
    VideoSourceItemOut,
    VideoSourceOut,
)
from app.services.video_source_service import VideoSourceService

router = APIRouter(
    prefix="/api/v1/video-sources", tags=["video-sources"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[VideoSourceOut])
async def list_sources(session: SessionDep) -> list[VideoSourceOut]:
    return await VideoSourceService.list(session)  # type: ignore[return-value]


@router.post("", response_model=VideoSourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(data: VideoSourceCreate, session: SessionDep) -> VideoSourceOut:
    return await VideoSourceService.create(  # type: ignore[return-value]
        session, data.name, data.source_type, data.config
    )


@router.get("/{source_id}", response_model=VideoSourceOut)
async def get_source(source_id: str, session: SessionDep) -> VideoSourceOut:
    return await VideoSourceService.get(session, source_id)  # type: ignore[return-value]


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: str, session: SessionDep):
    await VideoSourceService.delete(session, source_id)


@router.get("/{source_id}/items", response_model=list[VideoSourceItemOut])
async def list_items(source_id: str, session: SessionDep) -> list[VideoSourceItemOut]:
    return await VideoSourceService.list_items(session, source_id)  # type: ignore[return-value]


@router.post("/{source_id}/links", response_model=VideoSourceOut)
async def add_links(source_id: str, data: AddLinks, session: SessionDep) -> VideoSourceOut:
    return await VideoSourceService.add_links(session, source_id, data)  # type: ignore[return-value]


@router.delete("/{source_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(source_id: str, item_id: str, session: SessionDep):
    await VideoSourceService.delete_item(session, source_id, item_id)


@router.post("/{source_id}/run", response_model=RunResult)
async def run_source(source_id: str, req: RunRequest, session: SessionDep) -> RunResult:
    batch_id, job_count = await VideoSourceService.run(session, source_id, req)
    return RunResult(batch_id=batch_id, job_count=job_count)
