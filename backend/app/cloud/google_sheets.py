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


def _col_letter(idx0: int) -> str:
    """0-based chỉ số cột -> chữ cái A1 (0->A, 25->Z, 26->AA)."""
    s = ""
    n = idx0 + 1
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _q(worksheet: str | None, a1: str) -> str:
    """Ghép tên worksheet (quote nếu cần) + range A1."""
    if not worksheet:
        return a1
    safe = worksheet.replace("'", "''")
    return f"'{safe}'!{a1}"


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


async def read_header(token: str, spreadsheet_id: str, worksheet: str | None = None) -> dict:
    """Đọc hàng header (dòng 1). Trả {ok, header?(list[str]), error?}."""
    rng = _q(worksheet, "1:1")
    url = f"{_BASE}/{spreadsheet_id}/values/{rng}"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 200:
        vals = resp.json().get("values", [])
        return {"ok": True, "header": [str(h) for h in (vals[0] if vals else [])]}
    if resp.status_code in (401, 403):
        return {"ok": False, "error": "Không có quyền (share Editor cho service account?)"}
    if resp.status_code == 404:
        return {"ok": False, "error": "Không tìm thấy spreadsheet/worksheet"}
    return {"ok": False, "error": f"Google API lỗi HTTP {resp.status_code}"}


async def ensure_columns(
    token: str, spreadsheet_id: str, worksheet: str | None, columns: list[str]
) -> dict:
    """Đảm bảo các cột `columns` có trong header (thêm cột MỚI ở cuối nếu thiếu).

    KHÔNG đụng cột sẵn có. Trả {ok, index?(dict tên->cột 0-based), error?}.
    """
    hres = await read_header(token, spreadsheet_id, worksheet)
    if not hres["ok"]:
        return hres
    header = list(hres["header"])
    lower = {h.strip().lower(): i for i, h in enumerate(header)}
    missing = [c for c in columns if c.strip().lower() not in lower]
    if missing:
        first_new = len(header)
        header.extend(missing)
        a1 = f"{_col_letter(first_new)}1:{_col_letter(len(header) - 1)}1"
        rng = _q(worksheet, a1)
        url = f"{_BASE}/{spreadsheet_id}/values/{rng}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.put(
                url,
                params={"valueInputOption": "RAW"},
                headers={"Authorization": f"Bearer {token}"},
                json={"values": [missing]},
            )
        if resp.status_code not in (200, 201):
            if resp.status_code in (401, 403):
                return {"ok": False, "error": "Không có quyền GHI (cần Editor cho service account)"}
            return {"ok": False, "error": f"Ghi header lỗi HTTP {resp.status_code}"}
    index = {h.strip().lower(): i for i, h in enumerate(header)}
    return {"ok": True, "index": {c: index[c.strip().lower()] for c in columns}}


async def write_row_cells(
    token: str,
    spreadsheet_id: str,
    worksheet: str | None,
    row: int,
    cells: dict[int, str],
) -> dict:
    """Ghi nhiều ô trong 1 dòng `row` (1-based). `cells` = {cột 0-based: value}.

    Dùng values:batchUpdate, mỗi ô 1 range -> KHÔNG đụng ô khác cùng dòng. Trả {ok, error?}.
    """
    if not cells:
        return {"ok": True}
    data = [
        {"range": _q(worksheet, f"{_col_letter(c)}{row}"), "values": [[v]]}
        for c, v in sorted(cells.items())
    ]
    url = f"{_BASE}/{spreadsheet_id}/values:batchUpdate"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={"valueInputOption": "RAW", "data": data},
        )
    if resp.status_code in (200, 201):
        return {"ok": True}
    if resp.status_code in (401, 403):
        return {"ok": False, "error": "Không có quyền GHI (cần Editor cho service account)"}
    if resp.status_code == 404:
        return {"ok": False, "error": "Không tìm thấy spreadsheet/worksheet khi ghi"}
    return {"ok": False, "error": f"Ghi ô lỗi HTTP {resp.status_code}"}


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
