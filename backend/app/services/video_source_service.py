"""Video Source service (SPEC 02 §4.1, 10). Website chỉ tạo Job; Agent mới tải.

KHÔNG sửa engine/queue: Run = tạo Batch qua BatchService (mỗi item = 1 input row = 1 Job),
pipeline download (yt-dlp). Trạng thái item SUY từ job đã link khi đọc (không đụng engine).
"""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.models.enums import JobStatus
from app.models.job import Job
from app.models.project import Project
from app.models.video_source import VideoSource
from app.models.video_source_item import VideoSourceItem
from app.schemas.batch import BatchCreate
from app.schemas.video_source import AddLinks, RunRequest
from app.services.batch_service import BatchService

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
