"""Test Folder Watcher (SPEC 07): chuẩn hoá, coalesce, permission filter, reconcile theo allowed."""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

from agent.watcher import FolderWatcher, coalesce_events, normalize_event


class _Ev:
    """Stub sự kiện watchdog cho test chuẩn hoá."""

    def __init__(self, event_type: str, src: str, dest: str | None = None, is_dir: bool = False):
        self.event_type = event_type
        self.src_path = src
        self.dest_path = dest
        self.is_directory = is_dir


def test_normalize_filters_and_maps() -> None:
    assert normalize_event(_Ev("closed", "/x")) is None
    assert normalize_event(_Ev("opened", "/x")) is None
    created = normalize_event(_Ev("created", "/a/b.txt"))
    assert created["type"] == "created" and created["path"] == "/a/b.txt"
    moved = normalize_event(_Ev("moved", "/a/x", "/a/y"))
    assert moved["type"] == "moved" and moved["dest_path"] == "/a/y"


def test_coalesce_dedupes_keeping_latest() -> None:
    events = [
        {"type": "modified", "path": "/a", "ts": 1},
        {"type": "modified", "path": "/a", "ts": 2},
        {"type": "created", "path": "/b", "ts": 1},
    ]
    out = coalesce_events(events)
    assert len(out) == 2
    a = next(e for e in out if e["path"] == "/a")
    assert a["ts"] == 2


def _allowed_fn(roots: set[str]):
    def is_allowed(path: str) -> bool:
        rp = os.path.realpath(path)
        return any(rp == r or rp.startswith(r + os.sep) for r in roots)

    return is_allowed


def test_watcher_emits_real_event_and_filters_permission() -> None:
    root = tempfile.mkdtemp()
    roots = {os.path.realpath(root)}
    events: list[dict] = []
    watcher = FolderWatcher(events.append, _allowed_fn(roots))
    watcher.request(root, True)
    assert watcher.watched  # đang theo dõi root
    try:
        Path(root, "new.txt").write_text("x", encoding="utf-8")
        time.sleep(1.5)
    finally:
        watcher.stop()
    assert events, "phải nhận được ít nhất 1 sự kiện thật"
    assert {e["type"] for e in events} <= {"created", "modified", "deleted", "moved"}
    # Permission Manager: mọi sự kiện đều trong allowed
    assert all(_allowed_fn(roots)(e["path"]) for e in events)


def test_reconcile_stops_when_folder_removed_from_allowed() -> None:
    root = tempfile.mkdtemp()
    roots = {os.path.realpath(root)}
    watcher = FolderWatcher(lambda ev: None, _allowed_fn(roots))
    watcher.request(root, True)
    assert watcher.watched
    try:
        roots.clear()  # gỡ khỏi Allowed Folders
        watcher.reconcile()
        assert watcher.watched == []
    finally:
        watcher.stop()
