from __future__ import annotations

import logging

from fastapi import APIRouter, Body, Depends

from app.api.deps import SessionDep, require_owner
from app.api.ws.cookie_rpc import cookie_rpc
from app.core.errors import AppError
from app.orchestrator.agent_registry import registry
from app.services.cookie_service import CookieService
from app.services.event_service import EventService

router = APIRouter(
    prefix="/api/v1/cookies", tags=["cookies"], dependencies=[Depends(require_owner)]
)
log = logging.getLogger("cookies")

# status → (event type, log level). KHÔNG log nội dung cookie.
_STATUS_EVENT = {
    "valid": ("Cookie.Valid", None),
    "loaded": ("Cookie.Loaded", None),
    "expired": ("Cookie.Expired", "warn"),
    "invalid": ("Cookie.Invalid", "warn"),
    "missing": ("Cookie.Missing", "warn"),
    "permission_denied": ("Cookie.Invalid", "warn"),
    "authentication_failed": ("Cookie.AuthenticationFailed", "warn"),
}


async def _log_reloads() -> None:
    """Phát hiện file cookie MỚI/đổi (auto-detect, không cần restart) → log Cookie.Reloaded."""
    for ch in CookieService.detect_reloads():
        await EventService.record(
            entity_type="cookie",
            entity_id=str(ch.get("name") or ""),
            type="Cookie.Reloaded",
            data={"platform": ch.get("name")},  # KHÔNG log nội dung cookie
        )


@router.get("")
async def get_cookies() -> dict:
    """Cấu hình Cookie Manager + trạng thái nhẹ mỗi nền tảng + danh sách file .txt (cho Browse)."""
    cfg = CookieService.load()
    await _log_reloads()
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


async def _agent_test(name: str) -> dict | None:
    """Test cookie THẬT trên Agent (nơi duy nhất đọc cookie). None nếu thiếu agent."""
    params = CookieService.test_params(name)
    if not params:
        return None
    agents = registry.online_for("media.download")
    if not agents:
        return None
    try:
        return await cookie_rpc.call(agents[0].agent_id, params)
    except AppError as e:
        log.warning("agent cookie test '%s' lỗi: %s", name, e.code)
        return None


@router.post("/{name}/test")
async def test_cookie(name: str, session: SessionDep) -> dict:
    """Test 2 mức: Backend (định dạng/hết hạn) + Desktop Agent (THẬT: hiệu lực/đăng nhập).

    Trạng thái: valid | loaded | expired | invalid | missing | permission_denied |
    authentication_failed. KHÔNG mock, KHÔNG log nội dung cookie.
    """
    backend = CookieService.test(name)  # định dạng + hết hạn (status-only)
    agent = await _agent_test(name) if backend["status"] in ("loaded", "expired") else None
    result = dict(agent) if agent else dict(backend)
    result["source"] = "agent" if agent else "backend"
    status = result.get("status", "invalid")

    ev_type, level = _STATUS_EVENT.get(status, ("Cookie.Invalid", "warn"))
    ok = status in ("valid", "loaded")
    await EventService.record(
        entity_type="cookie",
        entity_id=name,
        type=ev_type,
        data={"platform": name, "status": status, "source": result["source"]},
        level=level,
    )
    await EventService.record(
        entity_type="cookie",
        entity_id=name,
        type="Cookie.Test.Success" if ok else "Cookie.Test.Failed",
        data={"platform": name, "status": status, "source": result["source"]},
        level=None if ok else "warn",
    )
    return result
