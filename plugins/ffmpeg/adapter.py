"""Adapter FFmpeg (capability video.ffmpeg) — chạy ffmpeg thật để dựng/convert/biến thể video (SPEC 06).

Hỗ trợ 2 cách:
- `args` đặt trong config (pipeline tĩnh, như cũ) HOẶC trong inputs (job vars — dùng cho biến thể).
- Token thay thế trong args: `{input}` -> file nguồn (resolve `source` tương đối data_dir),
  `{output}` -> `output_dir/<output_name>` (mặc định out.mp4). Tương thích ngược: không có
  source/token thì chạy y như cũ.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from agent.sdk import Adapter, PermanentError, StepContext


class FfmpegAdapter(Adapter):
    capability = "video.ffmpeg"

    def validate_config(self, config: dict) -> None:
        # args có thể đến từ inputs (job vars) -> không bắt buộc ở config. Chỉ kiểm kiểu nếu có.
        if "args" in config and not isinstance(config["args"], list):
            raise PermanentError("config.args phải là danh sách đối số ffmpeg")

    async def run(self, ctx: StepContext) -> None:
        ffmpeg = ctx.config.get("ffmpeg_path") or ctx.inputs.get("ffmpeg_path") or shutil.which(
            "ffmpeg"
        )
        if not ffmpeg:
            raise PermanentError("Không tìm thấy ffmpeg trong PATH hoặc config.ffmpeg_path")

        args = ctx.inputs.get("args") or ctx.config.get("args")
        if not isinstance(args, list) or not args:
            raise PermanentError("Thiếu args ffmpeg (đặt ở inputs hoặc config)")

        # Nguồn: resolve tương đối data_dir của Agent (asset.path lưu dạng tương đối).
        source = ctx.inputs.get("source") or ctx.config.get("source")
        input_path = ""
        if source:
            p = Path(source)
            full = p if p.is_absolute() else Path(ctx.data_dir) / p
            if not full.is_file():
                raise PermanentError(f"Không tìm thấy video nguồn: {source}")
            input_path = str(full)

        output_name = ctx.inputs.get("output_name") or ctx.config.get("output_name") or "out.mp4"
        output_path = str(ctx.output_dir / output_name)

        expanded = [
            str(a).replace("{input}", input_path).replace("{output}", output_path) for a in args
        ]
        command = [ffmpeg, "-y", "-hide_banner", *expanded]
        result = await ctx.process.run(command, ctx.timeout)
        if result.code != 0:
            raise PermanentError(f"ffmpeg lỗi (rc={result.code}): {result.stderr[-500:]}")
