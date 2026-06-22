"""Folder Watcher realtime (SPEC 05 §2, 07) dùng watchdog.

Nguyên tắc:
- Chỉ theo dõi thư mục nằm trong Allowed Folders; mọi sự kiện qua Permission Manager trước khi gửi.
- Agent chuẩn hoá sự kiện về 4 loại: created/modified/deleted/moved.
- Tự reconcile (start/stop) khi Allowed Folders hoặc danh sách watch thay đổi.
- Coalesce trùng lặp do bên gọi (connection) với debounce.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

WATCH_EVENT_TYPES = {"created", "modified", "deleted", "moved"}


def normalize_event(event: FileSystemEvent) -> dict | None:
    """Chuẩn hoá sự kiện watchdog -> dict; trả None nếu loại không hỗ trợ."""
    if event.event_type not in WATCH_EVENT_TYPES:
        return None
    out: dict = {
        "type": event.event_type,
        "path": event.src_path,
        "is_directory": bool(event.is_directory),
        "ts": time.time(),
    }
    dest = getattr(event, "dest_path", None)
    if dest:
        out["dest_path"] = dest
    return out


def event_key(ev: dict) -> tuple:
    return (ev["type"], ev["path"], ev.get("dest_path"))


def coalesce_events(events: list[dict]) -> list[dict]:
    """Gộp trùng theo (type, path, dest_path), giữ sự kiện mới nhất."""
    merged: dict[tuple, dict] = {}
    for ev in events:
        merged[event_key(ev)] = ev
    return list(merged.values())


class _Handler(FileSystemEventHandler):
    def __init__(self, emit: Callable[[FileSystemEvent], None]) -> None:
        self._emit = emit

    def on_any_event(self, event: FileSystemEvent) -> None:
        self._emit(event)


class FolderWatcher:
    """Theo dõi tập thư mục được yêu cầu ∩ Allowed Folders. Tự reconcile khi điều kiện đổi."""

    def __init__(self, sink: Callable[[dict], None], is_allowed: Callable[[str], bool]) -> None:
        self._observer = Observer()
        self._sink = sink
        self._is_allowed = is_allowed
        self._requested: set[str] = set()
        self._active: dict[str, object] = {}
        self._started = False

    def _on_event(self, event: FileSystemEvent) -> None:
        norm = normalize_event(event)
        if norm is None:
            return
        # Permission Manager: chỉ xử lý sự kiện trong Allowed Folders (SPEC 11 §5).
        if not self._is_allowed(norm["path"]):
            return
        if norm.get("dest_path") and not self._is_allowed(norm["dest_path"]):
            norm["dest_path"] = None
        self._sink(norm)

    def request(self, path: str, enable: bool) -> None:
        if enable:
            self._requested.add(path)
        else:
            self._requested.discard(path)
        self.reconcile()

    def reconcile(self) -> None:
        """Đồng bộ watch thực tế = (đã yêu cầu) ∩ (allowed) ∩ (là thư mục)."""
        desired = {p for p in self._requested if self._is_allowed(p) and os.path.isdir(p)}
        for path in list(self._active):
            if path not in desired:
                self._observer.unschedule(self._active.pop(path))
        for path in desired:
            if path not in self._active:
                self._ensure_started()
                self._active[path] = self._observer.schedule(
                    _Handler(self._on_event), path, recursive=True
                )

    def _ensure_started(self) -> None:
        if not self._started:
            self._observer.start()
            self._started = True

    @property
    def watched(self) -> list[str]:
        return sorted(self._active)

    def stop(self) -> None:
        if self._started:
            self._observer.stop()
            self._observer.join(timeout=2)
            self._started = False
        self._active.clear()
