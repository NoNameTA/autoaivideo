from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.api.deps import SessionDep, require_owner
from app.services.cookie_service import CookieService
from app.services.event_service import EventService

router = APIRouter(
    prefix="/api/v1/cookies", tags=["cookies"], dependencies=[Depends(require_owner)]
)


@router.get("")
async def get_cookies() -> dict:
    """Cấu hình Cookie Manager + trạng thái nhẹ mỗi nền tảng + danh sách file .txt (cho Browse)."""
    cfg = CookieService.load()
    return {
        "enabled": cfg.get("enabled", False),
        "cookie_dir": cfg.get("cookie_dir"),
        "platforms": CookieService.status(cfg),
        "cookie_files": CookieService.list_cookie_files(cfg.get("cookie_dir")),
    }


@router.put("")
async def save_cookies(body: dict = Body(...)) -> dict:
    """Lưu cấu hình (metadata: đường dẫn). KHÔNG lưu nội dung cookie."""
    saved = CookieService.save(body)
    return {
        "enabled": saved["enabled"],
        "cookie_dir": saved["cookie_dir"],
        "platforms": CookieService.status(saved),
        "cookie_files": CookieService.list_cookie_files(saved["cookie_dir"]),
    }


@router.post("/{name}/test")
async def test_cookie(name: str, session: SessionDep) -> dict:
    """Test Cookie THẬT (status-only): Loaded/Expired/Invalid/Missing/PermissionDenied + expires."""
    res = CookieService.test(name)
    ok = res["status"] == "loaded"
    await EventService.record(
        entity_type="cookie",
        entity_id=name,
        type="Cookie.Test.Success" if ok else "Cookie.Test.Failed",
        data={"platform": name, "status": res["status"]},  # KHÔNG log nội dung cookie
        level=None if ok else "warn",
    )
    return res
