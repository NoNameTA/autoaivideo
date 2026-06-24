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

_URL_RE = re.compile(r"https?://[^\s,;\"']+")
_DEFAULT_PROJECT = "Video Sources"

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
    values: list[list], url_column: str | None, title_column: str | None
) -> list[tuple[str, str | None]]:
    """Hàng đầu = header; lấy URL ở cột `url_column`. Thuần — dùng cho preview + import."""
    if not values:
        return []
    headers = [str(h) for h in values[0]]
    uidx = _col_index(headers, url_column)
    if uidx is None:
        raise ValidationAppError(f"Không tìm thấy cột '{url_column}' trong hàng header")
    tidx = _col_index(headers, title_column)
    out: list[tuple[str, str | None]] = []
    seen: set[str] = set()
    for row in values[1:]:
        if uidx >= len(row):
            continue
        m = _URL_RE.search(str(row[uidx]))
        if not m:
            continue
        url = m.group(0).rstrip(".,);")
        if url in seen:
            continue
        seen.add(url)
        title = None
        if tidx is not None and tidx < len(row):
            title = str(row[tidx]).strip() or None
        out.append((url, title))
    return out


class VideoSourceService:
    @staticmethod
    async def list(session: AsyncSession) -> list[VideoSource]:
        stmt = select(VideoSource).order_by(VideoSource.created_at.desc())
        return list((await session.execute(stmt)).scalars().all())

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
        start = src.item_count
        for i, (url, title) in enumerate(links):
            session.add(
                VideoSourceItem(source_id=src.id, seq=start + i, url=url, title=title)
            )
        src.item_count = start + len(links)
        src.status = "imported"
        await session.commit()
        await session.refresh(src)
        return src

    # ----- Google Sheets (phương án B: Backend đọc, Agent KHÔNG tham gia preview) -----
    @staticmethod
    async def _read_sheet_links(
        session: AsyncSession, source: VideoSource
    ) -> list[tuple[str, str | None]]:
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
            type="googlesheets.read",
            data={"rows": len(res["values"]), "spreadsheet_id": spreadsheet_id},
        )
        return _parse_sheet(res["values"], cfg.get("url_column"), cfg.get("title_column"))

    @staticmethod
    async def preview_sheet(session: AsyncSession, source_id: str) -> list[dict]:
        """Đọc Sheet trả PREVIEW (chưa tạo item, chưa tạo job)."""
        src = await VideoSourceService.get(session, source_id)
        links = await VideoSourceService._read_sheet_links(session, src)
        return [
            {"seq": i, "url": url, "title": title, "status": "pending"}
            for i, (url, title) in enumerate(links)
        ]

    @staticmethod
    async def import_from_sheet(session: AsyncSession, source_id: str) -> VideoSource:
        """Đọc Sheet -> tạo Video Source Item (KHÔNG tải video, KHÔNG tạo job)."""
        src = await VideoSourceService.get(session, source_id)
        links = await VideoSourceService._read_sheet_links(session, src)
        if not links:
            raise ValidationAppError("Sheet không có URL hợp lệ ở cột đã chọn")
        start = src.item_count
        for i, (url, title) in enumerate(links):
            session.add(
                VideoSourceItem(source_id=src.id, seq=start + i, url=url, title=title)
            )
        src.item_count = start + len(links)
        src.status = "imported"
        await session.commit()
        await session.refresh(src)
        await EventService.record(
            entity_type="video_source",
            entity_id=src.id,
            type="googlesheets.import",
            data={"imported": len(links)},
        )
        return src

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
        return batch.id, len(jobs)
