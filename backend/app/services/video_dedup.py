"""Dedup video theo Video ID → URL → hash(URL) (SPEC 02 §4.1, yêu cầu v1.0 §4).

Thuần (không I/O) để test dễ. `extract_video_id` nhận diện id theo nền tảng phổ biến
(TikTok/Facebook/YouTube/Instagram); không nhận ra → trả None (khi đó dùng url_hash).
"""
from __future__ import annotations

import hashlib
import re

# Mỗi pattern bắt 1 nhóm id theo nền tảng. Thứ tự không quan trọng (URL chỉ khớp 1 loại).
_ID_PATTERNS = [
    re.compile(r"tiktok\.com/.*?/video/(\d+)", re.I),
    re.compile(r"tiktok\.com/v/(\d+)", re.I),
    re.compile(r"facebook\.com/reel/(\d+)", re.I),
    re.compile(r"facebook\.com/.*?/videos/(\d+)", re.I),
    re.compile(r"facebook\.com/watch/?\?v=(\d+)", re.I),
    re.compile(r"fb\.watch/([\w-]+)", re.I),
    re.compile(r"youtube\.com/watch\?(?:.*&)?v=([\w-]{6,})", re.I),
    re.compile(r"youtu\.be/([\w-]{6,})", re.I),
    re.compile(r"youtube\.com/shorts/([\w-]{6,})", re.I),
    re.compile(r"instagram\.com/(?:reel|p|tv)/([\w-]+)", re.I),
]


def extract_video_id(url: str) -> str | None:
    """Trả video id (kèm tiền tố nền tảng để tránh đụng id giữa các nền tảng) hoặc None."""
    if not url:
        return None
    for pat in _ID_PATTERNS:
        m = pat.search(url)
        if m:
            host = "tiktok" if "tiktok" in pat.pattern else (
                "fb" if ("facebook" in pat.pattern or "fb.watch" in pat.pattern) else (
                    "yt" if "you" in pat.pattern else "ig"
                )
            )
            return f"{host}:{m.group(1)}"
    return None


def url_hash(url: str) -> str:
    """sha1 của URL đã chuẩn hoá nhẹ (bỏ khoảng trắng) — fallback khi không có video_id."""
    return hashlib.sha1((url or "").strip().encode("utf-8")).hexdigest()


def dedup_key(url: str) -> str:
    """Khoá dedup ổn định: video_id nếu có, ngược lại url_hash."""
    return extract_video_id(url) or url_hash(url)
