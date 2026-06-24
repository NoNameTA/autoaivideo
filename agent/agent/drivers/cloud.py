"""Driver `cloud` (SPEC 06 §9.1, 08 §5) — HTTP REST cho Cloud Adapter, tự gắn xác thực.

Hạ tầng chung trung lập nhà cung cấp: plugin chỉ gọi nghiệp vụ. Token ngắn hạn lấy JIT từ
Backend (qua ctx.get_credential), KHÔNG giữ secret. Plugin có thể dùng SDK riêng (vd gspread)
thay cho driver này nếu muốn (SPEC 06 §9.1).
"""
from __future__ import annotations

import httpx

from agent.sdk import PermanentError, TransientError


class CloudDriver:
    def __init__(self, base_url: str = "") -> None:
        self._base = base_url.rstrip("/")

    async def request(
        self,
        method: str,
        path: str,
        token: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        headers: dict | None = None,
        timeout: int = 30,
    ) -> dict:
        url = path if path.startswith("http") else f"{self._base}/{path.lstrip('/')}"
        hdr = {"Authorization": f"Bearer {token}", **(headers or {})}
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(method, url, params=params, json=json, headers=hdr)
        if resp.status_code == 429 or resp.status_code >= 500:
            raise TransientError(f"Cloud API {resp.status_code} (retry)")
        if resp.status_code in (401, 403):
            raise PermanentError("Cloud API 401/403 — cần cấp lại quyền")
        if resp.status_code >= 400:
            raise PermanentError(f"Cloud API lỗi {resp.status_code}: {resp.text[:200]}")
        if not resp.content:
            return {}
        return resp.json()
