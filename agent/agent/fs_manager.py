"""File Manager phía agent (SPEC 07) + Permission Manager (SPEC 11 §5).

Mọi thao tác chỉ trong Allowed Folders (do backend đẩy xuống qua config.update). Chống path
traversal bằng realpath + kiểm tra prefix. IO chạy trong thread để không chặn event loop.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import mimetypes
import os
import shutil
from pathlib import Path

_READ_LIMIT_DEFAULT = 1_048_576


class FsPermissionError(Exception):
    code = "FORBIDDEN"


class FsNotFound(Exception):
    code = "NOT_FOUND"


class FsOpError(Exception):
    code = "FS_ERROR"


class PermissionManager:
    def __init__(self) -> None:
        self._roots: list[str] = []

    def set_allowed(self, paths: list[str]) -> None:
        self._roots = [os.path.realpath(p) for p in paths]

    @property
    def roots(self) -> list[str]:
        return list(self._roots)

    def is_allowed(self, path: str) -> bool:
        try:
            rp = os.path.realpath(path)
        except OSError:
            return False
        return any(rp == root or rp.startswith(root + os.sep) for root in self._roots)

    def check(self, path: str) -> str:
        if not self.is_allowed(path):
            raise FsPermissionError(f"Đường dẫn ngoài Allowed Folders: {path}")
        return os.path.realpath(path)


def _meta(path: str) -> dict:
    st = os.stat(path)
    p = Path(path)
    is_dir = p.is_dir()
    return {
        "name": p.name,
        "path": str(p),
        "is_dir": is_dir,
        "size": st.st_size,
        "mtime": st.st_mtime,
        "ctime": st.st_ctime,
        "mime": None if is_dir else mimetypes.guess_type(p.name)[0],
    }


class FsManager:
    def __init__(self) -> None:
        self.perm = PermissionManager()

    async def handle(self, op: str, params: dict) -> dict:
        return await asyncio.to_thread(self._handle_sync, op, params)

    def _handle_sync(self, op: str, params: dict) -> dict:
        handler = getattr(self, f"_op_{op}", None)
        if handler is None:
            raise FsOpError(f"Thao tác không hỗ trợ: {op}")
        return handler(params)

    def _op_scan(self, params: dict) -> dict:
        path = self.perm.check(params["path"])
        if not os.path.exists(path):
            raise FsNotFound(path)
        if not os.path.isdir(path):
            raise FsOpError("Không phải thư mục")
        entries = []
        with os.scandir(path) as it:
            for entry in it:
                try:
                    entries.append(_meta(entry.path))
                except OSError:
                    continue
        entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
        return {"path": path, "entries": entries}

    def _op_metadata(self, params: dict) -> dict:
        path = self.perm.check(params["path"])
        if not os.path.exists(path):
            raise FsNotFound(path)
        meta = _meta(path)
        if not meta["is_dir"]:
            meta["checksum"] = hashlib.sha256(Path(path).read_bytes()).hexdigest()
        return meta

    def _op_read(self, params: dict) -> dict:
        path = self.perm.check(params["path"])
        if not os.path.isfile(path):
            raise FsNotFound(path)
        limit = int(params.get("max_bytes", _READ_LIMIT_DEFAULT))
        size = os.path.getsize(path)
        if size > limit:
            raise FsOpError(f"File quá lớn ({size} > {limit} bytes)")
        content = Path(path).read_bytes()
        try:
            return {"encoding": "text", "content": content.decode("utf-8"), "size": size}
        except UnicodeDecodeError:
            return {
                "encoding": "base64",
                "content": base64.b64encode(content).decode("ascii"),
                "size": size,
            }

    def _op_copy(self, params: dict) -> dict:
        src = self.perm.check(params["src"])
        dst = self.perm.check(params["dst"])
        if not os.path.exists(src):
            raise FsNotFound(src)
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return _meta(dst)

    def _op_move(self, params: dict) -> dict:
        src = self.perm.check(params["src"])
        dst = self.perm.check(params["dst"])
        if not os.path.exists(src):
            raise FsNotFound(src)
        shutil.move(src, dst)
        return _meta(dst)

    def _op_rename(self, params: dict) -> dict:
        path = self.perm.check(params["path"])
        if not os.path.exists(path):
            raise FsNotFound(path)
        new_name = params["new_name"]
        if os.sep in new_name or (os.altsep and os.altsep in new_name):
            raise FsOpError("new_name không được chứa dấu phân cách đường dẫn")
        dst = self.perm.check(os.path.join(os.path.dirname(path), new_name))
        os.rename(path, dst)
        return _meta(dst)

    def _op_delete(self, params: dict) -> dict:
        path = self.perm.check(params["path"])
        if not os.path.exists(path):
            raise FsNotFound(path)
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return {"deleted": path}


fs_manager = FsManager()
