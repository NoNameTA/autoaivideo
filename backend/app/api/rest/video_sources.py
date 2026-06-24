from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.video_source import (
    AddLinks,
    BvsEditRequest,
    BvsEditResult,
    RunRequest,
    RunResult,
    SheetCountResult,
    SheetImportResult,
    SheetPreviewRow,
    SheetReadRequest,
    VariationRequest,
    VariationResult,
    VideoSourceCreate,
    VideoSourceItemOut,
    VideoSourceOut,
    VideoSourceUpdate,
)
from app.services.variation_service import VariationService
from app.services.video_source_service import VideoSourceService

router = APIRouter(
    prefix="/api/v1/video-sources", tags=["video-sources"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[VideoSourceOut])
async def list_sources(session: SessionDep) -> list[VideoSourceOut]:
    return await VideoSourceService.list(session)  # type: ignore[return-value]


@router.get("/summary")
async def sources_summary(session: SessionDep) -> dict:
    """Tổng hợp số lượng theo nguồn + theo loại + tổng (UI không cần mở từng nguồn)."""
    return await VideoSourceService.summary(session)


@router.post("", response_model=VideoSourceOut, status_code=status.HTTP_201_CREATED)
async def create_source(data: VideoSourceCreate, session: SessionDep) -> VideoSourceOut:
    return await VideoSourceService.create(  # type: ignore[return-value]
        session, data.name, data.source_type, data.config
    )


@router.get("/{source_id}", response_model=VideoSourceOut)
async def get_source(source_id: str, session: SessionDep) -> VideoSourceOut:
    return await VideoSourceService.get(session, source_id)  # type: ignore[return-value]


@router.patch("/{source_id}", response_model=VideoSourceOut)
async def update_source(
    source_id: str, data: VideoSourceUpdate, session: SessionDep
) -> VideoSourceOut:
    return await VideoSourceService.update(  # type: ignore[return-value]
        session, source_id, data.name, data.config
    )


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


@router.post("/{source_id}/read-sheet", response_model=list[SheetPreviewRow])
async def read_sheet(
    source_id: str, session: SessionDep, req: SheetReadRequest | None = None
) -> list[SheetPreviewRow]:
    """Google Sheets mode — Backend đọc Sheet trả PREVIEW (Agent KHÔNG tham gia)."""
    r = req or SheetReadRequest()
    return await VideoSourceService.preview_sheet(  # type: ignore[return-value]
        session, source_id, r.filter, r.limit
    )


@router.post("/{source_id}/count-sheet", response_model=SheetCountResult)
async def count_sheet(
    source_id: str, session: SessionDep, req: SheetReadRequest | None = None
) -> SheetCountResult:
    """Đếm TRƯỚC khi import (tổng dòng / khớp filter / mới / trùng)."""
    r = req or SheetReadRequest()
    return await VideoSourceService.count_sheet(session, source_id, r.filter)  # type: ignore[return-value]


@router.post("/{source_id}/import-sheet", response_model=SheetImportResult)
async def import_sheet(
    source_id: str, session: SessionDep, req: SheetReadRequest | None = None
) -> SheetImportResult:
    r = req or SheetReadRequest()
    return await VideoSourceService.import_from_sheet(  # type: ignore[return-value]
        session, source_id, r.filter, r.limit
    )


@router.post("/{source_id}/run", response_model=RunResult)
async def run_source(source_id: str, req: RunRequest, session: SessionDep) -> RunResult:
    batch_id, job_count = await VideoSourceService.run(session, source_id, req)
    return RunResult(batch_id=batch_id, job_count=job_count)


@router.post("/{source_id}/items/{item_id}/variations", response_model=VariationResult)
async def create_variations(
    source_id: str, item_id: str, req: VariationRequest, session: SessionDep
) -> VariationResult:
    """Tạo N biến thể video (ffmpeg) từ 1 video đã tải của item."""
    batch_id, count = await VariationService.create_variations(
        session, source_id, item_id, req.count, req.model_dump()
    )
    return VariationResult(batch_id=batch_id, count=count)


@router.post("/{source_id}/items/{item_id}/bvs-edit", response_model=BvsEditResult)
async def bvs_edit(
    source_id: str, item_id: str, req: BvsEditRequest, session: SessionDep
) -> BvsEditResult:
    """Chỉnh 1 video đã tải bằng bộ công cụ Bulk Video Studio (qua agent BulkAuto)."""
    batch_id = await VariationService.create_bvs_edit(
        session, source_id, item_id, req.bulkauto_url, req.bvs_config
    )
    return BvsEditResult(batch_id=batch_id)
