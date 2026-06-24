"""Secret Provider trừu tượng (SPEC 11 §3.5) — backend lưu bí mật CÓ THỂ THAY THẾ.

Lõi đọc/ghi bí mật qua interface này → đổi backend (DB mã hoá / file cục bộ / Vault…) mà
KHÔNG sửa Adapter. V2.0 có 2 hiện thực: `db_store` (Fernet/MASTER_KEY) + `local_file` (dev/test).

Quy ước: cột `credentials.encrypted_secret` lưu **đại diện** do provider sinh ra:
- db_store : chuỗi Fernet token (đã mã hoá material).
- local_file: **đường dẫn file** (gitignored) — material nằm trong file, KHÔNG vào DB.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.errors import AppError


class SecretError(AppError):
    code = "SECRET_ERROR"
    status = 400


class SecretProvider(ABC):
    """get/put/delete material bí mật. Adapter & service chỉ gọi interface này."""

    name: str = ""

    @abstractmethod
    def put(self, material: str) -> str:
        """Lưu material, trả 'stored' để ghi vào `encrypted_secret`."""

    @abstractmethod
    def get(self, stored: str) -> str:
        """Lấy lại material gốc từ 'stored'."""

    def delete(self, stored: str) -> None:  # noqa: B027 - tuỳ chọn
        """Xoá material (mặc định no-op; local_file KHÔNG tự xoá file của owner)."""


class DbStoreProvider(SecretProvider):
    """Mã hoá material bằng Fernet (khoá `MASTER_KEY`), lưu token vào DB (prod ưu tiên)."""

    name = "db_store"

    def __init__(self, master_key: str) -> None:
        from cryptography.fernet import Fernet

        try:
            self._f = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)
        except Exception as e:  # noqa: BLE001
            raise SecretError(f"MASTER_KEY không hợp lệ (cần Fernet key): {e}") from None

    def put(self, material: str) -> str:
        return self._f.encrypt(material.encode("utf-8")).decode("ascii")

    def get(self, stored: str) -> str:
        from cryptography.fernet import InvalidToken

        try:
            return self._f.decrypt(stored.encode("ascii")).decode("utf-8")
        except InvalidToken:
            raise SecretError("Không giải mã được bí mật (MASTER_KEY sai?)") from None


class LocalFileProvider(SecretProvider):
    """Trỏ tới file bí mật gitignored trong `secrets_dir` (chỉ dev/test/single-machine)."""

    name = "local_file"

    def __init__(self, secrets_dir: str) -> None:
        self._base = Path(secrets_dir).resolve()

    def _resolve(self, stored: str) -> Path:
        # 'stored' = đường dẫn (tương đối secrets_dir hoặc tuyệt đối trong secrets_dir).
        p = Path(stored)
        full = (p if p.is_absolute() else self._base / p).resolve()
        # Chống path traversal: phải nằm trong secrets_dir (SPEC 11 §5).
        if os.path.commonpath([str(full), str(self._base)]) != str(self._base):
            raise SecretError("Đường dẫn bí mật phải nằm trong secrets_dir")
        return full

    def put(self, material: str) -> str:
        # material = đường dẫn do owner cung cấp; KHÔNG ghi nội dung bí mật vào DB.
        full = self._resolve(material)
        if not full.is_file():
            raise SecretError(f"Không tìm thấy file bí mật: {material}")
        return material

    def get(self, stored: str) -> str:
        full = self._resolve(stored)
        if not full.is_file():
            raise SecretError(f"File bí mật không tồn tại: {stored}")
        return full.read_text(encoding="utf-8")


def get_secret_provider() -> SecretProvider:
    """Chọn provider theo cấu hình (SPEC 11 §3.5): có MASTER_KEY -> db_store, không -> local_file.

    Cho phép auto-switch sang Credential Store khi owner cấu hình MASTER_KEY mà không sửa Adapter.
    """
    from app.core.config import get_settings

    s = get_settings()
    if s.master_key:
        return DbStoreProvider(s.master_key)
    return LocalFileProvider(s.secrets_dir)


def provider_by_backend(backend: str) -> SecretProvider:
    """Lấy đúng provider đã dùng lúc tạo 1 credential (ghi ở credential.metadata.backend)."""
    from app.core.config import get_settings

    s = get_settings()
    if backend == "db_store":
        if not s.master_key:
            raise SecretError("Credential dùng db_store nhưng thiếu MASTER_KEY")
        return DbStoreProvider(s.master_key)
    if backend == "local_file":
        return LocalFileProvider(s.secrets_dir)
    raise SecretError(f"Secret backend không hỗ trợ: {backend}")
