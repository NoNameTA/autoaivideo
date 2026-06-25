"""Adapter yt-dlp (capability media.download) — tải media thật bằng yt-dlp (SPEC 06, 14 free).

Bổ sung: **stream tiến độ realtime** qua `ctx.progress(pct, msg)` (parse `--progress-template`).
Chỉ sửa trong PLUGIN (không chạm Desktop Agent Core / kiến trúc Agent).
"""
from __future__ import annotations

import asyncio
import re
import sys

from agent.sdk import Adapter, PermanentError, StepContext

# Dòng tiến độ do yt-dlp in ra theo template bên dưới.
_PROG = re.compile(r"PROG\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)")
_PROG_TEMPLATE = (
    "PROG|%(progress._percent_str)s|%(progress._speed_str)s|"
    "%(progress._eta_str)s|%(progress.downloaded_bytes)s|%(progress.total_bytes)s"
)
_PCT = re.compile(r"([\d.]+)")


def _to_pct(s: str) -> int | None:
    m = _PCT.search(s or "")
    if not m:
        return None
    try:
        return max(0, min(100, int(float(m.group(1)))))
    except ValueError:
        return None


def _fmt_bytes(s: str) -> str:
    try:
        b = float(s)
    except (TypeError, ValueError):
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024 or unit == "GB":
            return f"{b:.1f}{unit}"
        b /= 1024
    return "?"


class YtDlpAdapter(Adapter):
    capability = "media.download"

    def validate_config(self, config: dict) -> None:
        args = config.get("args")
        if args is not None and not isinstance(args, list):
            raise PermanentError("config.args phải là danh sách")

    async def run(self, ctx: StepContext) -> None:
        url = ctx.inputs.get("url") or ctx.config.get("url")
        if not url:
            raise PermanentError("Thiếu 'url' (trong inputs hoặc config)")
        template = ctx.config.get("output_template", "%(title).80s.%(ext)s")
        extra = ctx.config.get("args", []) or []
        # Mặc định LUÔN ưu tiên VIDEO (tránh tải nhầm audio-only) -> mp4 ghép video+audio.
        # Nếu người dùng tự đặt -f/--format thì tôn trọng, không chèn.
        has_fmt = any(a in ("-f", "--format") for a in extra)
        fmt = [] if has_fmt else ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--newline", "--no-color",
            "--progress-template", _PROG_TEMPLATE,
            *fmt, *extra, "-o", template, url,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(ctx.output_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        tail: list[str] = []
        last = -1
        assert proc.stdout is not None
        async for raw in proc.stdout:
            line = raw.decode("utf-8", "replace").strip()
            m = _PROG.search(line)
            if m:
                pct_s, speed, eta, dl, total = (g.strip() for g in m.groups())
                pct = _to_pct(pct_s)
                if pct is not None and pct != last:
                    last = pct
                    msg = f"{speed} · ETA {eta} · {_fmt_bytes(dl)}/{_fmt_bytes(total)}"
                    ctx.progress(pct, msg)
            elif line:
                tail.append(line)
                tail[:] = tail[-15:]
        code = await proc.wait()
        if code != 0:
            raise PermanentError(f"yt-dlp lỗi (rc={code}): {' '.join(tail[-5:])[-400:]}")
        ctx.progress(100, "hoàn tất")
