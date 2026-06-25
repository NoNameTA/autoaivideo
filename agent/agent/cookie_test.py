"""Agent-side REAL cookie test (Cookie Manager).

Desktop Agent là nơi DUY NHẤT đọc nội dung cookie. Backend chỉ gửi đường dẫn + hosts + test_url.
KHÔNG mock, KHÔNG bịa cookie, KHÔNG vượt bảo mật trình duyệt — chỉ đọc file cookies.txt do người
dùng xuất hợp lệ.

2 mức kiểm tra THẬT:
1) Load bằng chính cookie-jar của yt-dlp (xác thực định dạng Netscape + suy hết hạn) — không mạng.
2) Nếu có `test_url`: chạy `yt-dlp --simulate` THẬT với cookie để kiểm đăng nhập/hiệu lực:
   thành công → valid; lỗi đăng nhập/bị chặn → authentication_failed.

Trả status: valid | expired | invalid | missing | permission_denied | authentication_failed.
KHÔNG trả/log NỘI DUNG cookie (chỉ số lượng + ngày hết hạn).
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path

# Dấu hiệu lỗi đăng nhập/bị chặn trong stderr yt-dlp → authentication_failed.
_AUTH_HINTS = (
    "log in", "login", "sign in", "private", "authentication", "not authorized",
    "requires authentication", "this video is unavailable", "use --cookies",
    "account", "restricted",
)


def _classify_format(cookie_path: str, hosts: list[str] | None) -> dict:
    """Mức 1: load cookie bằng yt-dlp + suy hết hạn (đọc trên máy Agent, không mạng)."""
    p = Path(cookie_path)
    if not p.is_file():
        return {"status": "missing", "message": "Không thấy file cookie trên máy Agent"}
    if not os.access(p, os.R_OK):
        return {"status": "permission_denied", "message": "Agent không có quyền đọc file cookie"}
    try:
        from yt_dlp.cookies import YoutubeDLCookieJar

        jar = YoutubeDLCookieJar(str(p))
        jar.load(ignore_discard=True, ignore_expires=True)
    except Exception as e:  # noqa: BLE001
        return {"status": "invalid", "message": f"File cookie sai định dạng: {type(e).__name__}"}
    cookies = list(jar)
    if not cookies:
        return {"status": "invalid", "message": "File cookie rỗng / không có cookie"}
    hosts = [h.lower() for h in (hosts or [])]
    relevant = [
        c for c in cookies
        if not hosts or any(h in (c.domain or "").lower() for h in hosts)
    ] or cookies
    now = time.time()
    exps = [c.expires for c in relevant if c.expires]
    future = [e for e in exps if e > now]
    if exps and not future:
        soon = time.strftime("%Y-%m-%d", time.localtime(max(exps)))
        return {"status": "expired", "message": "Cookie đã hết hạn", "expires": soon,
                "cookies": len(relevant)}
    expires = time.strftime("%Y-%m-%d", time.localtime(min(future))) if future else ""
    return {"status": "valid", "message": f"Agent đọc OK ({len(relevant)} cookie)",
            "expires": expires, "cookies": len(relevant)}


async def _live_probe(cookie_path: str, test_url: str) -> dict:
    """Mức 2: chạy yt-dlp --simulate THẬT với cookie để kiểm đăng nhập/hiệu lực."""
    cmd = [
        sys.executable, "-m", "yt_dlp", "--simulate", "--no-warnings", "--no-playlist",
        "--socket-timeout", "20", "--cookies", cookie_path, test_url,
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=60)
        code = proc.returncode
    except (TimeoutError, OSError) as e:
        return {"status": "invalid", "message": f"Không chạy được yt-dlp: {type(e).__name__}"}
    tail = (out or b"").decode("utf-8", "replace")[-600:]
    if code == 0:
        return {"status": "valid", "message": "yt-dlp dùng cookie + đọc video OK (đăng nhập OK)"}
    low = tail.lower()
    if any(h in low for h in _AUTH_HINTS):
        return {"status": "authentication_failed",
                "message": "Cookie không đăng nhập được / bị chặn (cần xuất lại cookie đăng nhập)"}
    return {"status": "invalid", "message": f"yt-dlp lỗi (rc={code}): {tail.splitlines()[-1][:120]}"
            if tail.strip() else f"yt-dlp lỗi (rc={code})"}


async def test(params: dict) -> dict:
    """Entry: params={cookie_path, hosts?, test_url?}. Trả status (status-only, KHÔNG nội dung)."""
    cookie_path = params.get("cookie_path") or ""
    hosts = params.get("hosts") or []
    test_url = (params.get("test_url") or "").strip()
    base = _classify_format(cookie_path, hosts)
    # Chỉ probe mạng khi format OK (valid) và có test_url do người dùng cấu hình.
    if base["status"] == "valid" and test_url:
        live = await _live_probe(cookie_path, test_url)
        live.setdefault("expires", base.get("expires", ""))
        live.setdefault("cookies", base.get("cookies"))
        return live
    return base
