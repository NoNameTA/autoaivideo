"""Adapter yt-dlp (capability media.download) — tải media thật bằng yt-dlp (SPEC 06, 14 free)."""

from __future__ import annotations

import sys

from agent.sdk import Adapter, PermanentError, StepContext


class YtDlpAdapter(Adapter):
    capability = "media.download"

    def validate_config(self, config: dict) -> None:
        # url có thể đến từ inputs nên không bắt buộc ở config.
        args = config.get("args")
        if args is not None and not isinstance(args, list):
            raise PermanentError("config.args phải là danh sách")

    async def run(self, ctx: StepContext) -> None:
        url = ctx.inputs.get("url") or ctx.config.get("url")
        if not url:
            raise PermanentError("Thiếu 'url' (trong inputs hoặc config)")
        template = ctx.config.get("output_template", "%(title).80s.%(ext)s")
        extra = ctx.config.get("args", []) or []
        command = [sys.executable, "-m", "yt_dlp", *extra, "-o", template, url]
        result = await ctx.process.run(command, ctx.timeout)
        if result.code != 0:
            raise PermanentError(f"yt-dlp lỗi (rc={result.code}): {result.stderr[-500:]}")
