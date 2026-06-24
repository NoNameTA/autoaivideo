"""Adapter Google Sheets (cloud-api) — SPEC 06 §11. Adapter ĐẦU TIÊN dùng Cloud Adapter Framework.

Dùng API Google Sheets chính thức qua `gspread` (Apache-2.0, free) với **access token ngắn hạn**
do Backend cấp JIT (ctx.get_credential) — KHÔNG giữ Service Account key ở Agent (SPEC 11 §3.3).
1 adapter phục vụ nhiều capability; đọc `ctx.capability` để biết operation. KHÔNG hard-code
spreadsheet/worksheet — tất cả qua config.
"""
from __future__ import annotations

import asyncio
import json

from agent.sdk import Adapter, PermanentError, StepContext, TransientError


class GoogleSheetsAdapter(Adapter):
    capabilities = [
        "cloud.google_sheets.read",
        "cloud.google_sheets.write",
        "cloud.google_sheets.append",
        "cloud.google_sheets.update_cell",
        "cloud.google_sheets.update_row",
    ]

    def validate_config(self, config: dict) -> None:
        if not config.get("spreadsheet_id"):
            raise PermanentError("config.spreadsheet_id là bắt buộc")
        if not config.get("credential_ref") and not config.get("connection_id"):
            raise PermanentError("Thiếu credential_ref/connection_id")

    async def run(self, ctx: StepContext) -> None:
        material = await ctx.get_credential()
        token = material["token"]
        op = ctx.capability.rsplit(".", 1)[-1]
        cfg = ctx.config
        try:
            result = await asyncio.to_thread(_run_sync, token, op, cfg)
        finally:
            token = None  # xoá token khỏi RAM sau op (SPEC 11 §3.3)
            material.clear()
        (ctx.output_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _run_sync(token: str, op: str, cfg: dict) -> dict:
    """Chạy gspread (đồng bộ) trong thread. Map lỗi -> Transient/Permanent."""
    try:
        import gspread
        from google.oauth2.credentials import Credentials
    except ImportError as e:
        raise PermanentError(f"Plugin google_sheets cần 'gspread' (pip install gspread): {e}") from None

    try:
        gc = gspread.authorize(Credentials(token=token))
        sh = gc.open_by_key(cfg["spreadsheet_id"])
        name = cfg.get("worksheet")
        ws = sh.worksheet(name) if name else sh.get_worksheet(0)
        vio = cfg.get("value_input_option", "USER_ENTERED")
        if op == "read":
            rng = cfg.get("range")
            values = ws.get(rng) if rng else ws.get_all_values()
            return {"op": op, "values": values, "rows": len(values)}
        if op == "write":
            ws.update(cfg.get("range", "A1"), cfg["values"], value_input_option=vio)
            return {"op": op, "status": "ok", "range": cfg.get("range", "A1")}
        if op == "append":
            ws.append_row(cfg["values"], value_input_option=vio)
            return {"op": op, "status": "ok"}
        if op == "update_cell":
            ws.update_acell(cfg["cell"], cfg["value"])
            return {"op": op, "status": "ok", "cell": cfg["cell"]}
        if op == "update_row":
            row = int(cfg["row_index"])
            ws.update(f"A{row}", [cfg["values"]], value_input_option=vio)
            return {"op": op, "status": "ok", "row": row}
        raise PermanentError(f"Operation không hỗ trợ: {op}")
    except KeyError as e:
        raise PermanentError(f"Thiếu config bắt buộc: {e}") from None
    except gspread.exceptions.APIError as e:  # type: ignore[attr-defined]
        status = getattr(e.response, "status_code", 0)
        if status == 429 or status >= 500:
            raise TransientError(f"Google Sheets {status} (retry)") from None
        if status in (401, 403):
            raise PermanentError("Google Sheets 401/403 — kiểm tra quyền share/scope") from None
        raise PermanentError(f"Google Sheets lỗi {status}") from None
    except gspread.exceptions.SpreadsheetNotFound:  # type: ignore[attr-defined]
        raise PermanentError("Không tìm thấy spreadsheet (sai id hoặc chưa share)") from None
    except gspread.exceptions.WorksheetNotFound:  # type: ignore[attr-defined]
        raise PermanentError("Không tìm thấy worksheet") from None
