"""Auto-Sync Google Sheets (v1.0+): web TỰ phát hiện sản phẩm mới trong Sheet.

Vòng lặp nền: mỗi nguồn google_sheets bật `auto_sync` sẽ được quét định kỳ
(`auto_sync_interval` giây). Import row MỚI (DEDUP đã bỏ video cũ -> KHÔNG tải lại).
Nếu `auto_run` bật thì tự tạo job tải cho các video chưa tải (giới hạn theo lô).

Additive: KHÔNG sửa engine/queue. Dùng lại VideoSourceService.import_from_sheet + run.
Lỗi 1 nguồn KHÔNG làm dừng cả vòng lặp.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select

from app.db.base import utcnow
from app.db.session import SessionLocal
from app.models.video_source import VideoSource
from app.models.video_source_item import VideoSourceItem
from app.schemas.video_source import RunRequest
from app.services.event_service import EventService

log = logging.getLogger("auto_sync")

_TICK_SECONDS = 30  # nhịp kiểm tra; mỗi nguồn tự tôn trọng interval riêng
_DEFAULT_INTERVAL = 600  # 10 phút nếu không cấu hình
_AUTO_RUN_CAP = 50  # tối đa video tự tải mỗi lượt (tránh quá tải)


def _due(cfg: dict, now: datetime) -> bool:
    last = cfg.get("last_auto_sync")
    if not last:
        return True
    try:
        prev = datetime.fromisoformat(last)
    except (ValueError, TypeError):
        return True
    interval = int(cfg.get("auto_sync_interval") or _DEFAULT_INTERVAL)
    return (now - prev).total_seconds() >= interval


class AutoSyncScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop())
            log.info("Auto-Sync scheduler started")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except Exception as e:  # noqa: BLE001 - không để hỏng vòng lặp
                log.warning("Auto-Sync tick lỗi: %s", type(e).__name__)
            await asyncio.sleep(_TICK_SECONDS)

    async def _tick(self) -> None:
        async with SessionLocal() as session:
            sources = (
                await session.execute(
                    select(VideoSource).where(VideoSource.source_type == "google_sheets")
                )
            ).scalars().all()
        now = utcnow()
        for src in sources:
            cfg = src.config or {}
            if not cfg.get("auto_sync") or not _due(cfg, now):
                continue
            await self._sync_one(src.id)

    async def _sync_one(self, source_id: str) -> None:
        # Import nội tại đã dedup -> chỉ thêm video MỚI; video cũ KHÔNG tải lại.
        from app.services.video_source_service import VideoSourceService

        try:
            async with SessionLocal() as session:
                res = await VideoSourceService.import_from_sheet(session, source_id, "all", None)
                src = res["source"]
                cfg = dict(src.config or {})
                cfg["last_auto_sync"] = utcnow().isoformat()
                src.config = cfg
                auto_run = bool(cfg.get("auto_run"))
                await session.commit()
            imported = res["imported"]
            await EventService.record(
                entity_type="video_source",
                entity_id=source_id,
                type="GoogleSheets.AutoSync",
                data={"imported": imported, "duplicates": res["duplicates"]},
            )
            if auto_run and imported > 0:
                await self._auto_run(source_id)
        except Exception as e:  # noqa: BLE001
            log.warning("Auto-Sync nguồn %s lỗi: %s", source_id, type(e).__name__)
            await EventService.record(
                entity_type="video_source",
                entity_id=source_id,
                type="GoogleSheets.AutoSync",
                data={"ok": False, "error": type(e).__name__},
                level="error",
            )

    async def _auto_run(self, source_id: str) -> None:
        """Tải các video CHƯA có job (mới import), giới hạn _AUTO_RUN_CAP mỗi lượt."""
        from app.services.video_source_service import VideoSourceService

        async with SessionLocal() as session:
            pending = (
                await session.execute(
                    select(VideoSourceItem.id)
                    .where(
                        VideoSourceItem.source_id == source_id,
                        VideoSourceItem.job_id.is_(None),
                    )
                    .order_by(VideoSourceItem.seq)
                    .limit(_AUTO_RUN_CAP)
                )
            ).scalars().all()
            if not pending:
                return
            await VideoSourceService.run(session, source_id, RunRequest(item_ids=list(pending)))


scheduler = AutoSyncScheduler()
