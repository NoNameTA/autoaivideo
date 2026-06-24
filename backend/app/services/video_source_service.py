"""Video Source service (SPEC 02 §4.1, 10). Website chỉ tạo Job; Agent mới tải.

KHÔNG sửa engine/queue: Run = tạo Batch qua BatchService (mỗi item = 1 input row = 1 Job),
pipeline download (yt-dlp). Trạng thái item SUY từ job đã link khi đọc (không đụng engine).
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cloud import google_sheets
from app.core.errors import NotFoundError, ValidationAppError
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.project import Project
from app.models.video_source import VideoSource
from app.models.video_source_item import VideoSourceItem
from app.schemas.batch import BatchCreate
from app.schemas.video_source import AddLinks, RunRequest
from app.services.batch_service import BatchService
from app.services.connection_service import ConnectionService
from app.services.credential_service import CredentialService
from app.services.event_service import EventService
from app.services.video_dedup import dedup_key, extract_video_id, url_hash

_URL_RE = re.compile(r"https?://[^\s,;\"']+")
_DEFAULT_PROJECT = "Video Sources"

# Bộ lọc import (thực hiện ở Backend, dựa trên cột Status write-back của chính Sheet).
IMPORT_FILTERS = {"all", "unprocessed", "failed", "not_downloaded"}
_DEFAULT_STATUS_COLUMN = "Status"


def _passes_filter(sheet_status: str, flt: str) -> bool:
    """sheet_status đã lower. unprocessed=chưa có Status; failed=Failed; not_downloaded=≠Done."""
    if flt == "unprocessed":
        return sheet_status == ""
    if flt == "failed":
        return sheet_status == "failed"
    if flt == "not_downloaded":
        return sheet_status != "done"
    return True  # all

# job.status -> item.status (suy khi đọc).
_JOB_TO_ITEM = {
    JobStatus.queued.value: "processing",
    JobStatus.running.value: "processing",
    JobStatus.completed.value: "done",
    JobStatus.failed.value: "failed",
    JobStatus.cancelled.value: "failed",
}


def _extract_links(data: AddLinks) -> list[tuple[str, str | None]]:
    """Tách (url, title) từ urls[] + text thô (paste nhiều dòng / txt / CSV)."""
    out: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    lines = list(data.urls)
    if data.text:
        lines += data.text.splitlines()
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        m = _URL_RE.search(line)
        if not m:
            continue
        url = m.group(0).rstrip(".,);")
        if url in seen:
            continue
        seen.add(url)
        # title = phần còn lại của dòng (vd cột CSV trước URL), nếu có.
        rest = (line[: m.start()] + line[m.end():]).strip(" ,;\t")
        out.append((url, rest or None))
    return out


def _col_index(headers: list[str], name: str | None) -> int | None:
    if not name:
        return None
    target = str(name).strip().lower()
    for i, h in enumerate(headers):
        if str(h).strip().lower() == target:
            return i
    return None


def _parse_sheet(
    values: list[list],
    url_column: str | None,
    title_column: str | None,
    status_column: str | None = None,
) -> list[dict]:
    """Hàng đầu = header; lấy URL ở cột `url_column`. Thuần — dùng cho preview + import.

    Trả list dict: url, title, sheet_row (1-based dòng THẬT), video_id, url_hash, sheet_status.
    Dedup TRONG sheet theo dedup_key (video_id→url_hash). `status_column` để lọc theo Status.
    """
    if not values:
        return []
    headers = [str(h) for h in values[0]]
    uidx = _col_index(headers, url_column)
    if uidx is None:
        raise ValidationAppError(f"Không tìm thấy cột '{url_column}' trong hàng header")
    tidx = _col_index(headers, title_column)
    sidx = _col_index(headers, status_column)
    out: list[dict] = []
    seen: set[str] = set()
    for i, row in enumerate(values[1:]):
        if uidx >= len(row):
            continue
        m = _URL_RE.search(str(row[uidx]))
        if not m:
            continue
        url = m.group(0).rstrip(".,);")
        key = dedup_key(url)
        if key in seen:
            continue
        seen.add(key)
        title = None
        if tidx is not None and tidx < len(row):
            title = str(row[tidx]).strip() or None
        sheet_status = ""
        if sidx is not None and sidx < len(row):
            sheet_status = str(row[sidx]).strip().lower()
        out.append(
            {
                "url": url,
                "title": title,
                "sheet_row": i + 2,  # +1 header, +1 vì 1-based
                "video_id": extract_video_id(url),
                "url_hash": url_hash(url),
                "sheet_status": sheet_status,
            }
        )
    return out


class VideoSourceService:
    @staticmethod
    async def list(session: AsyncSession) -> list[VideoSource]:
        stmt = select(VideoSource).order_by(VideoSource.created_at.desc())
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def summary(session: AsyncSession) -> dict:
        """Tổng hợp Video Sources: theo nguồn + theo loại + tổng (Ready/Running/Done/Failed/Dup).

        status item SUY từ job đã link (không đụng engine), gom 1 lượt cho mọi nguồn.
        """
        sources = list(
            (
                await session.execute(
                    select(VideoSource).order_by(VideoSource.created_at.desc())
                )
            ).scalars().all()
        )
        item_rows = (
            await session.execute(
                select(
                    VideoSourceItem.source_id, VideoSourceItem.status, VideoSourceItem.job_id
                )
            )
        ).all()
        job_ids = [jid for _, _, jid in item_rows if jid]
        jmap: dict[str, str] = {}
        if job_ids:
            jrows = (
                await session.execute(select(Job.id, Job.status).where(Job.id.in_(job_ids)))
            ).all()
            jmap = {jid: str(st) for jid, st in jrows}

        def _blank() -> dict:
            return {"pending": 0, "processing": 0, "done": 0, "failed": 0}

        per_source: dict[str, dict] = {s.id: _blank() for s in sources}
        for sid, status, jid in item_rows:
            resolved = _JOB_TO_ITEM.get(jmap.get(jid or ""), str(status))
            d = per_source.setdefault(sid, _blank())
            d[resolved] = d.get(resolved, 0) + 1

        by_type: dict[str, dict] = {}
        totals = {**_blank(), "items": 0, "sources": len(sources), "duplicate": 0}
        out_sources = []
        for s in sources:
            bs = per_source.get(s.id, _blank())
            items = sum(bs.values())
            out_sources.append(
                {
                    "id": s.id,
                    "name": s.name,
                    "source_type": s.source_type,
                    "status": s.status,
                    "item_count": s.item_count,
                    "duplicate_count": s.duplicate_count or 0,
                    "by_status": bs,
                }
            )
            t = by_type.setdefault(
                s.source_type, {"sources": 0, "items": 0, "duplicate": 0, **_blank()}
            )
            t["sources"] += 1
            t["items"] += items
            t["duplicate"] += s.duplicate_count or 0
            for k in bs:
                t[k] += bs[k]
            for k in bs:
                totals[k] += bs[k]
            totals["items"] += items
            totals["duplicate"] += s.duplicate_count or 0
        return {"totals": totals, "by_type": by_type, "sources": out_sources}

    @staticmethod
    async def get(session: AsyncSession, source_id: str) -> VideoSource:
        src = await session.get(VideoSource, source_id)
        if src is None:
            raise NotFoundError(f"Video Source '{source_id}' không tồn tại")
        return src

    @staticmethod
    async def create(
        session: AsyncSession, name: str, source_type: str, config: dict
    ) -> VideoSource:
        src = VideoSource(name=name, source_type=source_type, config=config, status="draft")
        session.add(src)
        await session.commit()
        await session.refresh(src)
        return src

    @staticmethod
    async def update(
        session: AsyncSession, source_id: str, name: str | None, config: dict | None
    ) -> VideoSource:
        src = await VideoSourceService.get(session, source_id)
        if name is not None:
            src.name = name
        if config is not None:
            src.config = config
        await session.commit()
        await session.refresh(src)
        return src

    @staticmethod
    async def delete(session: AsyncSession, source_id: str) -> None:
        src = await VideoSourceService.get(session, source_id)
        await session.delete(src)
        await session.commit()

    @staticmethod
    async def add_links(session: AsyncSession, source_id: str, data: AddLinks) -> VideoSource:
        src = await VideoSourceService.get(session, source_id)
        links = _extract_links(data)
        if not links:
            raise ValidationAppError("Không tìm thấy URL hợp lệ (http/https)")
        vids, hashes = await VideoSourceService._existing_keys(session, source_id)
        start = src.item_count
        imported = 0
        duplicates = 0
        for url, title in links:
            vid, h = extract_video_id(url), url_hash(url)
            if (vid and vid in vids) or (h in hashes):
                duplicates += 1
                continue
            session.add(
                VideoSourceItem(
                    source_id=src.id,
                    seq=start + imported,
                    url=url,
                    title=title,
                    video_id=vid,
                    url_hash=h,
                )
            )
            imported += 1
            if vid:
                vids.add(vid)
            hashes.add(h)
        src.item_count = start + imported
        src.duplicate_count = (src.duplicate_count or 0) + duplicates
        if imported:
            src.status = "imported"
        await session.commit()
        await session.refresh(src)
        return src

    # ----- Google Sheets (phương án B: Backend đọc, Agent KHÔNG tham gia preview) -----
    @staticmethod
    async def _read_sheet_rows(session: AsyncSession, source: VideoSource) -> list[dict]:
        """Đọc + parse Sheet -> list dict (url/title/sheet_row/video_id/url_hash/sheet_status)."""
        cfg = source.config or {}
        conn_id = cfg.get("connection_id")
        if not conn_id:
            raise ValidationAppError("Nguồn Google Sheets thiếu connection_id")
        conn = await ConnectionService.get(session, conn_id)
        if not conn.credential_id:
            raise ValidationAppError("Connection chưa gắn credential")
        cred = await CredentialService.get(session, conn.credential_id)
        token, _ = await CredentialService.mint_token(session, cred)
        settings = conn.settings or {}
        spreadsheet_id = cfg.get("spreadsheet_id") or settings.get("spreadsheet_id")
        worksheet = cfg.get("worksheet") or settings.get("worksheet")
        res = await google_sheets.read_values(token, spreadsheet_id, worksheet)
        if not res["ok"]:
            raise ValidationAppError(res["error"])
        await EventService.record(
            entity_type="video_source",
            entity_id=source.id,
            type="GoogleSheets.Read",
            data={"rows": len(res["values"]), "spreadsheet_id": spreadsheet_id},
        )
        return _parse_sheet(
            res["values"],
            cfg.get("url_column"),
            cfg.get("title_column"),
            cfg.get("status_column", _DEFAULT_STATUS_COLUMN),
        )

    @staticmethod
    def _apply_filter_limit(rows: list[dict], flt: str, limit: int | None) -> list[dict]:
        out = [r for r in rows if _passes_filter(r["sheet_status"], flt)]
        if limit is not None and limit > 0:
            out = out[:limit]
        return out

    @staticmethod
    async def _existing_keys(session: AsyncSession, source_id: str) -> tuple[set[str], set[str]]:
        """(video_id set, url_hash set) của các item đã có trong nguồn — để dedup."""
        rows = (
            await session.execute(
                select(VideoSourceItem.video_id, VideoSourceItem.url_hash).where(
                    VideoSourceItem.source_id == source_id
                )
            )
        ).all()
        vids = {v for v, _ in rows if v}
        hashes = {h for _, h in rows if h}
        return vids, hashes

    @staticmethod
    async def preview_sheet(
        session: AsyncSession, source_id: str, flt: str = "all", limit: int | None = None
    ) -> list[dict]:
        """Đọc Sheet trả PREVIEW (chưa tạo item, chưa tạo job). Có filter + limit."""
        src = await VideoSourceService.get(session, source_id)
        rows = await VideoSourceService._read_sheet_rows(session, src)
        rows = VideoSourceService._apply_filter_limit(rows, flt, limit)
        return [
            {
                "seq": i,
                "url": r["url"],
                "title": r["title"],
                "status": "pending",
                "sheet_row": r["sheet_row"],
            }
            for i, r in enumerate(rows)
        ]

    @staticmethod
    async def count_sheet(session: AsyncSession, source_id: str, flt: str = "all") -> dict:
        """Đếm TRƯỚC khi import: tổng dòng, khớp filter, mới (sẽ import) vs trùng (dedup)."""
        src = await VideoSourceService.get(session, source_id)
        rows = await VideoSourceService._read_sheet_rows(session, src)
        matched = [r for r in rows if _passes_filter(r["sheet_status"], flt)]
        vids, hashes = await VideoSourceService._existing_keys(session, source_id)
        new_count = 0
        for r in matched:
            if (r["video_id"] and r["video_id"] in vids) or (r["url_hash"] in hashes):
                continue
            new_count += 1
        return {
            "total_rows": len(rows),
            "matched": len(matched),
            "new": new_count,
            "duplicate": len(matched) - new_count,
        }

    @staticmethod
    async def import_from_sheet(
        session: AsyncSession, source_id: str, flt: str = "all", limit: int | None = None
    ) -> dict:
        """Đọc Sheet -> tạo Item (KHÔNG tải/tạo job). Filter + limit + DEDUP (video_id/url/hash)."""
        if flt not in IMPORT_FILTERS:
            raise ValidationAppError(f"Filter không hợp lệ: {flt}")
        src = await VideoSourceService.get(session, source_id)
        rows = await VideoSourceService._read_sheet_rows(session, src)
        rows = VideoSourceService._apply_filter_limit(rows, flt, limit)
        if not rows:
            raise ValidationAppError("Không có dòng nào khớp filter (hoặc Sheet trống)")
        vids, hashes = await VideoSourceService._existing_keys(session, source_id)
        start = src.item_count
        imported = 0
        duplicates = 0
        for r in rows:
            vid, h = r["video_id"], r["url_hash"]
            if (vid and vid in vids) or (h in hashes):
                duplicates += 1
                continue
            session.add(
                VideoSourceItem(
                    source_id=src.id,
                    seq=start + imported,
                    url=r["url"],
                    title=r["title"],
                    sheet_row=r["sheet_row"],
                    video_id=vid,
                    url_hash=h,
                )
            )
            imported += 1
            if vid:
                vids.add(vid)
            hashes.add(h)
        src.item_count = start + imported
        src.duplicate_count = (src.duplicate_count or 0) + duplicates
        if imported:
            src.status = "imported"
        await session.commit()
        await session.refresh(src)
        await EventService.record(
            entity_type="video_source",
            entity_id=src.id,
            type="GoogleSheets.Import",
            data={"imported": imported, "duplicates": duplicates, "filter": flt},
        )
        return {"source": src, "imported": imported, "duplicates": duplicates, "matched": len(rows)}

    @staticmethod
    async def list_items(session: AsyncSession, source_id: str) -> list[VideoSourceItem]:
        await VideoSourceService.get(session, source_id)
        items = list(
            (
                await session.execute(
                    select(VideoSourceItem)
                    .where(VideoSourceItem.source_id == source_id)
                    .order_by(VideoSourceItem.seq)
                )
            ).scalars().all()
        )
        # Suy status từ job đã link (không commit -> không đụng DB).
        job_ids = [it.job_id for it in items if it.job_id]
        if job_ids:
            rows = (
                await session.execute(select(Job.id, Job.status).where(Job.id.in_(job_ids)))
            ).all()
            jmap = {jid: str(st) for jid, st in rows}
            for it in items:
                if it.job_id and it.job_id in jmap:
                    it.status = _JOB_TO_ITEM.get(jmap[it.job_id], it.status)
        return items

    @staticmethod
    async def delete_item(session: AsyncSession, source_id: str, item_id: str) -> None:
        src = await VideoSourceService.get(session, source_id)
        item = await session.get(VideoSourceItem, item_id)
        if item is None or item.source_id != source_id:
            raise NotFoundError(f"Item '{item_id}' không thuộc nguồn này")
        await session.delete(item)
        src.item_count = max(0, src.item_count - 1)
        await session.commit()

    @staticmethod
    async def _default_project_id(session: AsyncSession) -> str:
        existing = (
            await session.execute(select(Project).where(Project.name == _DEFAULT_PROJECT))
        ).scalar_one_or_none()
        if existing is not None:
            return existing.id
        proj = Project(name=_DEFAULT_PROJECT, default_pipeline="video_download")
        session.add(proj)
        await session.flush()
        return proj.id

    @staticmethod
    async def run(session: AsyncSession, source_id: str, req: RunRequest) -> tuple[str, int]:
        src = await VideoSourceService.get(session, source_id)
        items = await VideoSourceService.list_items(session, source_id)
        if req.item_ids is not None:
            wanted = set(req.item_ids)
            items = [it for it in items if it.id in wanted]
        if not items:
            raise ValidationAppError("Không có video nào được chọn để chạy")

        project_id = req.project_id or await VideoSourceService._default_project_id(session)
        inputs = [{"url": it.url, "title": it.title or ""} for it in items]
        batch = await BatchService.create(
            session,
            project_id,
            BatchCreate(name=f"{src.name} ({len(items)})", inputs=inputs, pipeline=req.pipeline),
        )
        # Map job theo seq (BatchService tạo job seq=index inputs) -> link vào item.
        jobs = list(
            (
                await session.execute(
                    select(Job).where(Job.batch_id == batch.id).order_by(Job.seq)
                )
            ).scalars().all()
        )
        for item, job in zip(items, jobs, strict=False):
            item.job_id = job.id
            item.status = "processing"
        src.status = "running"
        await session.commit()
        # Tạo sẵn cột write-back 1 lần (nếu nguồn google_sheets bật writeback) — tránh race header.
        if src.source_type == "google_sheets" and (src.config or {}).get("writeback"):
            from app.services.sheet_writeback import ensure_writeback_columns

            await ensure_writeback_columns(session, src)
        return batch.id, len(jobs)
