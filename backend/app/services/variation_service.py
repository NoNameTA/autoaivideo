"""Video Variations (1 video -> N biến thể) bằng ffmpeg THẬT (SPEC 06).

Lấy 1 video nguồn (asset đã tải của 1 item) -> tạo N job pipeline `ffmpeg_variant`, mỗi job 1
biến thể với công thức ffmpeg khác nhau. KHÔNG sửa engine/queue — tái dùng BatchService.

Biến thể tự động (KHÔNG cần file ngoài): spin (đổi tốc độ/lật/zoom/màu) + đổi tỉ lệ (9:16/1:1/16:9).
Tuỳ chọn (cần file): caption (chữ), watermark (ảnh logo), music (nhạc nền). Map đúng dòng video gốc.
"""
from __future__ import annotations

import os
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationAppError
from app.models.asset import Asset
from app.models.video_source_item import VideoSourceItem
from app.schemas.batch import BatchCreate
from app.services.batch_service import BatchService
from app.services.event_service import EventService

# Tỉ lệ -> (rộng, cao).
_RATIOS: dict[str, tuple[int, int]] = {
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "16:9": (1920, 1080),
}
# Tham số biến đổi theo chỉ số biến thể (đảm bảo N bản KHÁC nhau rõ).
_SPEEDS = [1.0, 0.97, 1.03, 0.95, 1.05, 0.98, 1.02, 0.96, 1.04, 0.99]
_ZOOMS = [1.0, 0.94, 0.92, 0.96, 0.90]
_EQS = [(0.0, 1.0), (0.03, 1.06), (-0.03, 1.1), (0.05, 0.95), (-0.02, 1.12)]
_VIDEO_EXT = (".mp4", ".webm", ".mkv", ".mov", ".m4v")


def _find_font() -> str | None:
    for p in (r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf"):
        if os.path.isfile(p):
            return p.replace("\\", "/").replace(":", "\\:")  # escape cho drawtext
    return None


def _escape_drawtext(text: str) -> str:
    return (
        text.replace("\\", "").replace(":", " ").replace("'", "").replace("%", "")
        .replace("\n", " ").strip()
    )


def build_recipes(opts: dict, count: int, title: str | None = None) -> list[dict]:
    """Sinh `count` công thức ffmpeg (args + output_name). Dùng token {input}/{output}."""
    if count < 1 or count > 50:
        raise ValidationAppError("Số biến thể phải từ 1 đến 50")
    ratios: Sequence[str] = opts.get("ratios") or (
        ["9:16", "1:1", "16:9"] if opts.get("ratio") else []
    )
    for r in ratios:
        if r not in _RATIOS:
            raise ValidationAppError(f"Tỉ lệ không hỗ trợ: {r}")
    use_spin = opts.get("spin", True)
    caption = (opts.get("caption_text") or (title if opts.get("caption") else "") or "").strip()
    watermark = opts.get("watermark_path") or ""
    music = opts.get("music_path") or ""
    if watermark and not os.path.isfile(watermark):
        raise ValidationAppError(f"Không tìm thấy file logo/watermark: {watermark}")
    if music and not os.path.isfile(music):
        raise ValidationAppError(f"Không tìm thấy file nhạc: {music}")

    recipes: list[dict] = []
    for k in range(count):
        vf: list[str] = []
        af: list[str] = []
        labels: list[str] = []
        if use_spin:
            s = _SPEEDS[k % len(_SPEEDS)]
            if abs(s - 1.0) > 1e-3:
                vf.append(f"setpts={1.0 / s:.4f}*PTS")
                af.append(f"atempo={s:.4f}")
                labels.append(f"speed{s:g}")
            if k % 2 == 1:
                vf.append("hflip")
                labels.append("flip")
            z = _ZOOMS[k % len(_ZOOMS)]
            if z < 0.999:
                vf.append(f"crop=iw*{z}:ih*{z}")
                labels.append(f"zoom{z:g}")
            b, sat = _EQS[k % len(_EQS)]
            if b or sat != 1.0:
                vf.append(f"eq=brightness={b}:saturation={sat}")
                labels.append("color")
        if ratios:
            r = ratios[k % len(ratios)]
            w, h = _RATIOS[r]
            vf.append(f"scale={w}:{h}:force_original_aspect_ratio=increase")
            vf.append(f"crop={w}:{h}")
            labels.append(r)
        if caption:
            font = _find_font()
            if font:
                vf.append(
                    f"drawtext=fontfile='{font}':text='{_escape_drawtext(caption)[:60]}'"
                    ":x=(w-tw)/2:y=h*0.85:fontsize=42:fontcolor=white:box=1:boxcolor=black@0.45"
                    ":boxborderw=8"
                )
                labels.append("caption")
        vf_str = ",".join(vf) if vf else "null"

        args: list[str] = ["-i", "{input}"]
        if watermark:
            args += ["-i", watermark]
        if music:
            args += ["-i", music]
        if watermark:
            wm_in = 1
            music_in = 2 if music else None
            fc = f"[0:v]{vf_str}[base];[base][{wm_in}:v]overlay=W-w-12:12[v]"
            args += ["-filter_complex", fc, "-map", "[v]"]
            args += ["-map", f"{music_in}:a"] if music_in else ["-map", "0:a?"]
            labels.append("logo")
        else:
            args += ["-vf", vf_str]
            if music:
                args += ["-map", "0:v", "-map", "1:a", "-shortest"]
                labels.append("music")
            elif af:
                args += ["-af", ",".join(af)]
        if music:
            labels.append("music")
        args += [
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-movflags", "+faststart", "{output}",
        ]
        recipes.append(
            {
                "args": args,
                "output_name": f"variant_{k + 1}.mp4",
                "label": "+".join(labels) or "copy",
            }
        )
    return recipes


class VariationService:
    @staticmethod
    async def _source_asset(session: AsyncSession, item: VideoSourceItem) -> Asset:
        if not item.job_id:
            raise ValidationAppError("Item chưa tải xong (chưa có video nguồn để chỉnh)")
        assets = (
            await session.execute(
                select(Asset).where(Asset.job_id == item.job_id).order_by(Asset.size.desc())
            )
        ).scalars().all()
        vid = next(
            (a for a in assets if a.path and a.path.lower().endswith(_VIDEO_EXT) and a.size > 0),
            None,
        )
        if vid is None:
            if assets:  # có asset nhưng là audio/không phải video
                raise ValidationAppError(
                    "Video này tải về CHỈ CÓ AUDIO — chọn item, bấm Run Workflow tải lại rồi chỉnh."
                )
            raise ValidationAppError(
                "Item này chưa có file video (hoặc tải ở phiên cũ) — Run Workflow tải lại rồi chỉnh."
            )
        return vid

    @staticmethod
    async def create_variations(
        session: AsyncSession,
        source_id: str,
        item_id: str,
        count: int,
        options: dict,
        project_id: str | None = None,
    ) -> tuple[str, int]:
        from app.services.video_source_service import VideoSourceService

        item = await session.get(VideoSourceItem, item_id)
        if item is None or item.source_id != source_id:
            raise NotFoundError(f"Item '{item_id}' không thuộc nguồn này")
        asset = await VariationService._source_asset(session, item)
        recipes = build_recipes(options, count, title=item.title)

        inputs = [
            {
                "source": asset.path,
                "args": r["args"],
                "output_name": r["output_name"],
                "title": f"{(item.title or 'video')[:60]} — {r['label']}",
            }
            for r in recipes
        ]
        pid = project_id or await VideoSourceService._default_project_id(session)
        batch = await BatchService.create(
            session,
            pid,
            BatchCreate(
                name=f"Biến thể: {(item.title or 'video')[:40]} ({count})",
                inputs=inputs,
                pipeline="ffmpeg_variant",
            ),
        )
        await session.commit()
        await EventService.record(
            entity_type="video_source",
            entity_id=source_id,
            type="Video.Variations",
            data={"item_id": item_id, "count": count, "ratios": options.get("ratios")},
        )
        return batch.id, count

    @staticmethod
    async def create_bvs_edit(
        session: AsyncSession,
        source_id: str,
        item_id: str,
        bulkauto_url: str | None,
        bvs_config: dict | None,
        project_id: str | None = None,
    ) -> str:
        """Chỉnh 1 video đã tải bằng bộ công cụ Bulk Video Studio (qua agent BulkAuto)."""
        from app.services.video_source_service import VideoSourceService

        item = await session.get(VideoSourceItem, item_id)
        if item is None or item.source_id != source_id:
            raise NotFoundError(f"Item '{item_id}' không thuộc nguồn này")
        asset = await VariationService._source_asset(session, item)
        row: dict = {"source": asset.path, "title": f"BVS — {(item.title or 'video')[:60]}"}
        if bulkauto_url:
            row["bulkauto_url"] = bulkauto_url
        if bvs_config:
            row["bvs_config"] = bvs_config
        pid = project_id or await VideoSourceService._default_project_id(session)
        batch = await BatchService.create(
            session,
            pid,
            BatchCreate(
                name=f"BVS edit: {(item.title or 'video')[:40]}",
                inputs=[row],
                pipeline="bvs_edit",
            ),
        )
        await session.commit()
        await EventService.record(
            entity_type="video_source",
            entity_id=source_id,
            type="Video.BvsEdit",
            data={"item_id": item_id},
        )
        return batch.id
