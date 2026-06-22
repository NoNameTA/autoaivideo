"""Adapter FFmpeg (capability video.ffmpeg) — chạy ffmpeg thật để dựng/convert video (SPEC 06)."""

from __future__ import annotations

import shutil

from agent.sdk import Adapter, PermanentError, StepContext


class FfmpegAdapter(Adapter):
    capability = "video.ffmpeg"

    def validate_config(self, config: dict) -> None:
        args = config.get("args")
        if not isinstance(args, list) or not args:
            raise PermanentError("config.args (danh sách đối số ffmpeg) là bắt buộc")

    async def run(self, ctx: StepContext) -> None:
        ffmpeg = ctx.config.get("ffmpeg_path") or shutil.which("ffmpeg")
        if not ffmpeg:
            raise PermanentError("Không tìm thấy ffmpeg trong PATH hoặc config.ffmpeg_path")
        command = [ffmpeg, "-y", "-hide_banner", *ctx.config["args"]]
        result = await ctx.process.run(command, ctx.timeout)
        if result.code != 0:
            raise PermanentError(f"ffmpeg lỗi (rc={result.code}): {result.stderr[-500:]}")
