"""Healthcheck Google Sheets phía Backend (SPEC 06 §9.3) — gọi API chính thức (D7), không bypass.

Thao tác đọc/ghi thật chạy ở Agent (gspread); ở đây chỉ kiểm tra auth + tới được spreadsheet
cho nút Test kết nối.
"""
from __future__ import annotations

import httpx

_BASE = "https://sheets.googleapis.com/v4/spreadsheets"


async def healthcheck(token: str, spreadsheet_id: str) -> dict:
    """GET metadata nhẹ. Trả {ok, title?, error?}."""
    if not spreadsheet_id:
        return {"ok": False, "error": "Thiếu spreadsheet_id trong settings của connection"}
    url = f"{_BASE}/{spreadsheet_id}"
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            url,
            params={"fields": "spreadsheetId,properties.title"},
            headers={"Authorization": f"Bearer {token}"},
        )
    if resp.status_code == 200:
        title = (resp.json().get("properties") or {}).get("title", "")
        return {"ok": True, "title": title}
    if resp.status_code in (401, 403):
        return {"ok": False, "error": "Không có quyền (share spreadsheet cho service account?)"}
    if resp.status_code == 404:
        return {"ok": False, "error": "Không tìm thấy spreadsheet (sai spreadsheet_id?)"}
    return {"ok": False, "error": f"Google API lỗi HTTP {resp.status_code}"}
