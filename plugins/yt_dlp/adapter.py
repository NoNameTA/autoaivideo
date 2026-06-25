"""Adapter yt-dlp (capability media.download) — tải media thật bằng yt-dlp (SPEC 06, 14 free).

Bổ sung: **stream tiến độ realtime** qua `ctx.progress(pct, msg)` (parse `--progress-template`).
Auto-cookie: nếu video tải về **chỉ có audio** (TikTok/FB chặn video) thì **tự thử lại bằng cookie
trình duyệt** (mặc định Chrome) — lấy được video thì thay thế, không thì GIỮ bản cũ (không hỏng job).
Chỉ sửa trong PLUGIN (không chạm Desktop Agent Core).
"""
from __future__ import annotations

import asyncio
import re
import shutil
import sys
from pathlib import Path

from agent.sdk import Adapter, PermanentError, StepContext

_PROG = re.compile(r"PROG\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)")
_PROG_TEMPLATE = (
    "PROG|%(progress._percent_str)s|%(progress._speed_str)s|"
    "%(progress._eta_str)s|%(progress.downloaded_bytes)s|%(progress.total_bytes)s"
)
_PCT = re.compile(r"([\d.]+)")
_AUDIO_EXT = (".mp3", ".m4a", ".aac", ".opus", ".ogg", ".wav", ".flac")
_MEDIA_EXT = (".mp4", ".webm", ".mkv", ".mov", ".m4v", *_AUDIO_EXT)
_DEFAULT_COOKIE_BROWSER = "chrome"
# Đặt file cookies.txt vào đây -> dùng được kể cả khi Chrome đang MỞ (không bị khoá DB).
_DEFAULT_COOKIE_FILE = r"C:\AIVideoPlatform\.secrets\cookies.txt"


def _cookie_args(ctx: StepContext, browser: str) -> list[str]:
    """Ưu tiên file cookies.txt (không bị khoá khi Chrome mở); không có thì đọc từ trình duyệt."""
    import os

    f = ctx.config.get("cookies_file") or ctx.inputs.get("cookies_file") or _DEFAULT_COOKIE_FILE
    if f and os.path.isfile(f):
        return ["--cookies", f]
    return ["--cookies-from-browser", browser]


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


def _find_media(folder: Path) -> Path | None:
    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in _MEDIA_EXT and not p.name.endswith(".part")
    ]
    return max(files, key=lambda p: p.stat().st_size) if files else None


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
        has_fmt = any(a in ("-f", "--format") for a in extra)
        fmt = [] if has_fmt else ["-f", "bv*+ba/b", "--merge-output-format", "mp4"]
        user_cookie = any("cookies" in str(a).lower() for a in extra)
        cookie_browser = (
            ctx.config.get("cookies_browser")
            or ctx.inputs.get("cookies_browser")
            or _DEFAULT_COOKIE_BROWSER
        )

        base = [
            sys.executable, "-m", "yt_dlp", "--newline", "--no-color",
            "--progress-template", _PROG_TEMPLATE,
        ]
        out_args = ["-o", template, url]

        # Lần 1: tải bình thường (tôn trọng -f/cookies của người dùng nếu có).
        code, tail = await self._attempt(ctx, [*base, *fmt, *extra, *out_args], ctx.output_dir)
        if code != 0:
            raise PermanentError(f"yt-dlp lỗi (rc={code}): {' '.join(tail[-5:])[-400:]}")

        out = _find_media(ctx.output_dir)
        # Audio-only + có cookie fallback + người dùng chưa tự đặt cookie -> thử lại bằng cookie.
        if out and out.suffix.lower() in _AUDIO_EXT and cookie_browser and not user_cookie:
            await self._cookie_retry(ctx, base, fmt, extra, out_args, cookie_browser, out)

        ctx.progress(100, "hoàn tất")

    async def _cookie_retry(
        self, ctx: StepContext, base: list, fmt: list, extra: list,
        out_args: list, browser: str, audio_file: Path,
    ) -> None:
        """Tải lại vào thư mục tạm bằng cookie trình duyệt; có VIDEO thì thay bản audio."""
        ctx.progress(0, f"Video chỉ có audio — thử lại bằng cookie {browser}…")
        tmp = ctx.output_dir / "_cookie_try"
        tmp.mkdir(parents=True, exist_ok=True)
        try:
            cmd = [*base, *fmt, *_cookie_args(ctx, browser), *extra, *out_args]
            code, tail = await self._attempt(ctx, cmd, tmp)
            newf = _find_media(tmp)
            if code == 0 and newf and newf.suffix.lower() not in _AUDIO_EXT:
                # Lấy được VIDEO -> thay thế bản audio.
                audio_file.unlink(missing_ok=True)
                shutil.move(str(newf), str(ctx.output_dir / newf.name))
                ctx.progress(0, "Đã lấy được video bằng cookie ✓")
            else:
                hint = " ".join(tail[-3:])[-200:]
                ctx.progress(0, f"Cookie chưa lấy được video (đóng {browser} rồi thử lại?) {hint}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    async def _attempt(
        self, ctx: StepContext, cmd: list[str], cwd: Path
    ) -> tuple[int, list[str]]:
        proc = await asyncio.create_subprocess_exec(
            *cmd, cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
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
                    ctx.progress(pct, f"{speed} · ETA {eta} · {_fmt_bytes(dl)}/{_fmt_bytes(total)}")
            elif line:
                tail.append(line)
                tail[:] = tail[-15:]
        return await proc.wait(), tail
