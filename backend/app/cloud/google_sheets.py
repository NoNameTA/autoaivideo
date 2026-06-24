"""Google Sheets phía Backend (SPEC 06 §9.3, 02 §4.1) — gọi API chính thức (D7), không bypass.

- `healthcheck`: Test kết nối.
- `read_values`: ĐỌC danh sách dòng cho **Preview/Import** (phương án B: Website→Backend→Adapter,
  Agent KHÔNG tham gia preview).
Thao tác GHI/tải video vẫn ở Agent (gspread / yt-dlp).
"""
from __future__ import annotations

import httpx

_BASE = "https://sheets.googleapis.com/v4/spreadsheets"
_READ_RANGE = "A1:Z10000"


async def read_values(token: str, spreadsheet_id: str, worksheet: str | None = None) -> dict:
    """Đọc rows (list[list[str]]) từ worksheet. Trả {ok, values?, error?}."""
    if not spreadsheet_id:
        return {"ok": False, "error": "Thiếu spreadsheet_id"}
    rng = f"{worksheet}!{_READ_RANGE}" if worksheet else _READ_RANGE
    url = f"{_BASE}/{spreadsheet_id}/values/{rng}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200:
        return {"ok": True, "values": resp.json().get("values", [])}
    if resp.status_code in (401, 403):
        return {"ok": False, "error": "Không có quyền (share spreadsheet cho service account?)"}
    if resp.status_code == 404:
        return {"ok": False, "error": "Không tìm thấy spreadsheet/worksheet"}
    return {"ok": False, "error": f"Google API lỗi HTTP {resp.status_code}"}


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
