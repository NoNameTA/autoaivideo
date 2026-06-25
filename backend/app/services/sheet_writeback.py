"""Google Sheets WRITE-BACK (v1.0 §1). Sau khi Job (từ nguồn google_sheets) kết thúc,
ghi kết quả về ĐÚNG DÒNG trong worksheet đích.

Nguyên tắc:
- Phương án B (Backend ghi qua Sheets API) — đồng nhất với đọc, KHÔNG đụng engine/pipeline.
- Map theo `sheet_row` THẬT (không index tạm). KHÔNG ghi đè cột Link Video.
- Tự tạo cột write-back nếu thiếu (ensure_columns) — KHÔNG đụng cột sẵn có.
- KHÔNG bao giờ log token/credential. Lỗi write-back KHÔNG được làm hỏng Job/engine.

KHÔNG upload, KHÔNG `Output URL`. Ghi **Output Path** (đường dẫn video trên máy Windows) +
**Output Filename** (tên file). Video chỉ lưu cục bộ; muốn upload sau này = cài thêm Plugin Upload
(không phải sửa write-back này).
"""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cloud import google_sheets
from app.db.session import SessionLocal
from app.models.asset import Asset
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.video_source import VideoSource
from app.models.video_source_item import VideoSourceItem
from app.services import output_path as op_resolve
from app.services.connection_service import ConnectionService
from app.services.credential_service import CredentialService
from app.services.event_service import EventService

log = logging.getLogger("sheet_writeback")

# Thứ tự cột write-back (tự tạo nếu thiếu). KHÔNG upload → Output Path/Filename, KHÔNG Output URL.
WRITEBACK_COLUMNS = [
    "Status",
    "Output Path",
    "Output Filename",
    "Completed Time",
    "Duration",
    "Error",
]
_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def _enabled(source: VideoSource) -> bool:
    return bool((source.config or {}).get("writeback"))


def _target_worksheet(source: VideoSource) -> str | None:
    cfg = source.config or {}
    return cfg.get("writeback_worksheet") or cfg.get("worksheet")


def _fmt_duration(ms: int | None) -> str:
    if not ms or ms < 0:
        return ""
    s = ms / 1000.0
    if s < 60:
        return f"{s:.1f}s"
    m, sec = divmod(int(s), 60)
    return f"{m}m{sec:02d}s"


async def _resolve(
    session: AsyncSession, source: VideoSource
) -> tuple[str, str, str | None]:
    """(token, spreadsheet_id, worksheet) cho write-back. Raise nếu thiếu cấu hình."""
    cfg = source.config or {}
    conn = await ConnectionService.get(session, cfg["connection_id"])
    cred = await CredentialService.get(session, conn.credential_id)
    token, _ = await CredentialService.mint_token(session, cred, [_SHEETS_SCOPE])
    settings = conn.settings or {}
    spreadsheet_id = cfg.get("spreadsheet_id") or settings.get("spreadsheet_id")
    return token, spreadsheet_id, _target_worksheet(source)


async def ensure_writeback_columns(session: AsyncSession, source: VideoSource) -> None:
    """Tạo sẵn cột write-back 1 LẦN lúc Run (tránh race khi nhiều job ghi header cùng lúc)."""
    if not _enabled(source):
        return
    try:
        token, sid, ws = await _resolve(session, source)
        res = await google_sheets.ensure_columns(token, sid, ws, WRITEBACK_COLUMNS)
        if not res["ok"]:
            log.warning("ensure_writeback_columns lỗi: %s", res.get("error"))
    except Exception as e:  # noqa: BLE001 - không để hỏng Run
        log.warning("ensure_writeback_columns exception: %s", type(e).__name__)


async def on_job_terminal(job_id: str) -> None:
    """Hook gọi khi Job chuyển terminal. Tự mở session riêng; KHÔNG raise ra engine."""
    try:
        async with SessionLocal() as session:
            await _writeback_job(session, job_id)
    except Exception as e:  # noqa: BLE001 - write-back KHÔNG được làm hỏng engine
        log.warning("write-back job %s lỗi: %s", job_id, type(e).__name__)
        await EventService.record(
            entity_type="job",
            entity_id=job_id,
            type="GoogleSheets.Update",
            data={"ok": False, "error": f"write-back lỗi: {type(e).__name__}"},
            level="error",
        )


async def _writeback_job(session: AsyncSession, job_id: str) -> None:
    item = (
        await session.execute(
            select(VideoSourceItem).where(VideoSourceItem.job_id == job_id)
        )
    ).scalar_one_or_none()
    if item is None or item.sheet_row is None:
        return
    source = await session.get(VideoSource, item.source_id)
    if source is None or source.source_type != "google_sheets" or not _enabled(source):
        return

    job = (
        await session.execute(
            select(Job)
            .where(Job.id == job_id)
            .options(selectinload(Job.steps), selectinload(Job.assets))
        )
    ).scalar_one_or_none()
    if job is None or job.status not in (JobStatus.completed, JobStatus.failed):
        return

    ok = job.status == JobStatus.completed
    assets: list[Asset] = list(job.assets)
    # Output Path = đường dẫn video trên máy (dest_folder đã nhúng nếu Plugin copy vào Output
    # Folder, nếu không thì data_dir/asset.path). KHÔNG upload, KHÔNG URL.
    output_path = ""
    output_filename = ""
    if ok and assets:
        dest_folder = (job.vars or {}).get("dest_folder")
        info = op_resolve.from_assets(assets, dest_folder)
        if info:
            output_path = info["output_path"]
            output_filename = info["output_filename"]

    starts = [s.started_at for s in job.steps if s.started_at]
    ends = [s.finished_at for s in job.steps if s.finished_at]
    start = min(starts) if starts else job.created_at
    end = max(ends) if ends else job.updated_at
    dur_ms = int((end - start).total_seconds() * 1000) if (start and end) else None
    err = ""
    if not ok:
        err = job.error or next((s.error for s in job.steps if s.error), "") or "Download lỗi"

    values = {
        "Status": "Done" if ok else "Failed",
        "Output Path": output_path,
        "Output Filename": output_filename,
        "Completed Time": end.strftime("%Y-%m-%d %H:%M:%S") if end else "",
        "Duration": _fmt_duration(dur_ms),
        "Error": err,
    }

    token, sid, ws = await _resolve(session, source)
    ens = await google_sheets.ensure_columns(token, sid, ws, WRITEBACK_COLUMNS)
    if not ens["ok"]:
        await EventService.record(
            entity_type="job",
            entity_id=job_id,
            type="GoogleSheets.Update",
            data={"ok": False, "error": ens["error"], "row": item.sheet_row},
            level="error",
        )
        return
    cells = {ens["index"][name]: val for name, val in values.items()}
    wr = await google_sheets.write_row_cells(token, sid, ws, item.sheet_row, cells)
    data = {
        "ok": wr["ok"],
        "row": item.sheet_row,
        "status": values["Status"],
        "worksheet": ws,
    }
    if not wr["ok"]:
        data["error"] = wr["error"]
    await EventService.record(
        entity_type="job",
        entity_id=job_id,
        type="GoogleSheets.Update",
        data=data,
        level=None if wr["ok"] else "error",
    )
