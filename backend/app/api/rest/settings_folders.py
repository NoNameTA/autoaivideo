from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.api.deps import require_owner
from app.services.output_settings import OutputSettings

router = APIRouter(
    prefix="/api/v1/settings", tags=["settings"], dependencies=[Depends(require_owner)]
)


@router.get("/folders")
async def get_folders() -> dict:
    """Output Folders: Download / Export / Temp (KHÔNG upload — video lưu trên máy)."""
    return OutputSettings.load()


@router.put("/folders")
async def save_folders(body: dict = Body(...)) -> dict:
    """Lưu Output Folders. Thư mục trống = giữ mặc định. Agent đọc qua job inputs."""
    return OutputSettings.save(body)
