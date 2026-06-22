"""Test File Manager phía agent (SPEC 07) + Permission Manager (SPEC 11 §5) — thao tác file thật."""

from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

from agent.fs_manager import FsManager, FsPermissionError


def _manager(root: str) -> FsManager:
    m = FsManager()
    m.perm.set_allowed([root])
    return m


def _run(coro):
    return asyncio.run(coro)


def test_permission_denied_outside_root() -> None:
    root = tempfile.mkdtemp()
    m = _manager(root)
    outside = "C:\\Windows\\win.ini" if os.name == "nt" else "/etc/hosts"
    with pytest.raises(FsPermissionError):
        m.perm.check(outside)


def test_scan_and_metadata() -> None:
    root = tempfile.mkdtemp()
    m = _manager(root)
    Path(root, "a.txt").write_text("hello", encoding="utf-8")
    os.mkdir(os.path.join(root, "sub"))

    res = _run(m.handle("scan", {"path": root}))
    names = {e["name"] for e in res["entries"]}
    assert {"a.txt", "sub"} <= names

    meta = _run(m.handle("metadata", {"path": os.path.join(root, "a.txt")}))
    assert meta["size"] == 5
    assert "checksum" in meta and len(meta["checksum"]) == 64


def test_read_copy_move_rename_delete() -> None:
    root = tempfile.mkdtemp()
    m = _manager(root)
    src = os.path.join(root, "f.txt")
    Path(src).write_text("data", encoding="utf-8")

    read = _run(m.handle("read", {"path": src}))
    assert read["encoding"] == "text" and read["content"] == "data"

    _run(m.handle("copy", {"src": src, "dst": os.path.join(root, "copy.txt")}))
    assert os.path.exists(os.path.join(root, "copy.txt"))

    _run(m.handle("rename", {"path": os.path.join(root, "copy.txt"), "new_name": "renamed.txt"}))
    assert os.path.exists(os.path.join(root, "renamed.txt"))

    _run(
        m.handle(
            "move",
            {"src": os.path.join(root, "renamed.txt"), "dst": os.path.join(root, "moved.txt")},
        )
    )
    assert os.path.exists(os.path.join(root, "moved.txt"))

    _run(m.handle("delete", {"path": os.path.join(root, "moved.txt")}))
    assert not os.path.exists(os.path.join(root, "moved.txt"))


def test_operation_outside_root_denied() -> None:
    root = tempfile.mkdtemp()
    m = _manager(root)
    outside = "C:\\Windows\\win.ini" if os.name == "nt" else "/etc/hosts"
    with pytest.raises(FsPermissionError):
        _run(m.handle("read", {"path": outside}))
