"""Media Check — phân loại file tải về VIDEO / AUDIO_ONLY / INVALID bằng ffprobe THẬT.

Bước BỔ SUNG sau Download (additive). KHÔNG đổi engine/queue/agent-core/adapter. Phân loại DỰA
TRÊN STREAM THỰC TẾ (ffprobe), KHÔNG dựa đuôi file / tên file / MIME.

- VIDEO       : có ít nhất 1 video stream THẬT (bỏ qua attached_pic = ảnh bìa của file audio).
- AUDIO_ONLY  : chỉ có audio stream, không có video stream thật (vd .mp4 nhưng không có hình).
- INVALID     : ffprobe không đọc được / file hỏng / size 0 / không có stream.

Status-only: KHÔNG đọc/log nội dung nhạy cảm.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.asset import Asset
from app.models.video_source_item import VideoSourceItem
from app.services.event_service import EventService

log = logging.getLogger("media_check")

VIDEO = "video"
AUDIO_ONLY = "audio_only"
INVALID = "invalid"

# ffprobe đóng gói kèm BVS (fallback khi không có trong PATH).
_BVS_FFPROBE = (
    r"C:\Users\PC\Downloads\Telegram Desktop\GOI_CHUYEN_MAY_BulkVideoStudio"
    r"\GOI_CHUYEN_MAY_BulkVideoStudio\CAN_CAI\ffmpeg\bin\ffprobe.exe"
)
_VIDEO_EXT = (".mp4", ".webm", ".mkv", ".mov", ".m4v")


def ffprobe_bin() -> str | None:
    """Tìm ffprobe: PATH → ffprobe kèm BVS. None nếu không có."""
    found = shutil.which("ffprobe")
    if found:
        return found
    if os.path.isfile(_BVS_FFPROBE):
        return _BVS_FFPROBE
    return None


def probe(abs_path: str) -> str:
    """Trả VIDEO | AUDIO_ONLY | INVALID dựa trên stream thật (ffprobe)."""
    if not abs_path or not os.path.isfile(abs_path):
        return INVALID
    try:
        if os.path.getsize(abs_path) == 0:
            return INVALID
    except OSError:
        return INVALID
    binary = ffprobe_bin()
    if not binary:
        # Không có ffprobe → không kết luận được; coi như INVALID để KHÔNG đưa nhầm vào edit.
        log.warning("Không tìm thấy ffprobe — không kiểm tra được media")
        return INVALID
    try:
        out = subprocess.run(
            [binary, "-v", "error", "-show_entries", "stream=codec_type,disposition",
             "-of", "json", abs_path],
            capture_output=True, text=True, timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return INVALID
    if out.returncode != 0:
        return INVALID
    try:
        data = json.loads(out.stdout or "{}")
    except json.JSONDecodeError:
        return INVALID
    streams = data.get("streams") or []
    if not streams:
        return INVALID
    has_real_video = False
    has_audio = False
    for s in streams:
        ctype = s.get("codec_type")
        if ctype == "video":
            # attached_pic = ảnh bìa (vd mp3 có cover) → KHÔNG tính là video thật.
            if int((s.get("disposition") or {}).get("attached_pic", 0)) != 1:
                has_real_video = True
        elif ctype == "audio":
            has_audio = True
    if has_real_video:
        return VIDEO
    if has_audio:
        return AUDIO_ONLY
    return INVALID


def resolve_asset_path(asset_path: str) -> str:
    """asset.path (tương đối data_dir Agent) → đường dẫn tuyệt đối để ffprobe."""
    rel = (asset_path or "").replace("\\", "/")
    if os.path.isabs(rel):
        return os.path.normpath(rel)
    return os.path.abspath(os.path.join(get_settings().data_dir, rel))


def pick_asset(assets: list[Asset]) -> Asset | None:
    withp = [a for a in assets if a.path and (a.size or 0) > 0]
    if not withp:
        return None
    # Ưu tiên file đuôi video (nếu có), nếu không lấy file lớn nhất — ffprobe quyết định thật.
    vids = [a for a in withp if a.path.lower().endswith(_VIDEO_EXT)]
    pool = vids or withp
    return max(pool, key=lambda a: a.size or 0)


async def check_item(
    session: AsyncSession, item: VideoSourceItem, commit: bool = True
) -> str | None:
    """Media Check 1 item ĐÃ tải xong: ffprobe asset → set item.media_type + log Media.*.

    Trả media_type (hoặc None nếu chưa có asset). KHÔNG raise (không làm hỏng luồng gọi).
    """
    if not item.job_id:
        return None
    try:
        assets = (
            await session.execute(select(Asset).where(Asset.job_id == item.job_id))
        ).scalars().all()
        asset = pick_asset(list(assets))
        if asset is None:
            return None
        await EventService.record(
            entity_type="video_source", entity_id=item.source_id,
            type="Media.Check.Start", data={"item_id": item.id},
        )
        # ffprobe chạy ở thread riêng để KHÔNG block event loop.
        mt = await asyncio.to_thread(probe, resolve_asset_path(asset.path))
        item.media_type = mt
        if commit:
            await session.commit()
        ev = {VIDEO: "Media.Video", AUDIO_ONLY: "Media.AudioOnly", INVALID: "Media.Invalid"}[mt]
        await EventService.record(
            entity_type="video_source", entity_id=item.source_id, type=ev,
            data={"item_id": item.id, "media_type": mt},
            level="warn" if mt != VIDEO else None,
        )
        await EventService.record(
            entity_type="video_source", entity_id=item.source_id,
            type="Media.Check.Success", data={"item_id": item.id, "media_type": mt},
        )
        return mt
    except Exception as e:  # noqa: BLE001 - media check KHÔNG được làm hỏng luồng gọi
        log.warning("media check item %s lỗi: %s", item.id, type(e).__name__)
        await EventService.record(
            entity_type="video_source", entity_id=item.source_id,
            type="Media.Check.Failed", data={"item_id": item.id, "error": type(e).__name__},
            level="error",
        )
        return None
