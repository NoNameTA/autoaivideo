"""Output Folders (Download/Export/Temp) — KHÔNG upload, video chỉ lưu trên máy Windows.

Cấu hình lưu ở 1 file JSON `<data_dir>/output_folders.json` (đồng pattern với Cookie Manager —
không đụng DB schema). Desktop Agent đọc các thư mục này QUA job inputs (Backend nhúng `dest_folder`
khi tạo job Download/Edit) → KHÔNG hard-code trong Plugin.

Mặc định:
- Download Folder: `C:\\Users\\PC\\Videos\\video gốc`  (video tải về)
- Export Folder:   `C:\\Users\\PC\\Videos\\video da sua` (video đã chỉnh/Export)
- Temp Folder:     `C:\\Users\\PC\\Videos\\temp`
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import get_settings

_CONFIG_NAME = "output_folders.json"
_DEFAULTS = {
    "download_folder": r"C:\Users\PC\Videos\video gốc",
    "export_folder": r"C:\Users\PC\Videos\video da sua",
    "temp_folder": r"C:\Users\PC\Videos\temp",
}
_KEYS = ("download_folder", "export_folder", "temp_folder")


class OutputSettings:
    @staticmethod
    def _config_path() -> Path:
        return Path(get_settings().data_dir) / _CONFIG_NAME

    @staticmethod
    def load() -> dict:
        """Đọc cấu hình thư mục (tự dùng mặc định khi chưa có file)."""
        cfg = dict(_DEFAULTS)
        path = OutputSettings._config_path()
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                for k in _KEYS:
                    if data.get(k):
                        cfg[k] = str(data[k]).strip()
            except (json.JSONDecodeError, OSError):
                pass
        return cfg

    @staticmethod
    def save(cfg: dict) -> dict:
        """Ghi cấu hình thư mục. Thư mục trống = giữ mặc định (không cho rỗng)."""
        out = dict(_DEFAULTS)
        for k in _KEYS:
            v = str(cfg.get(k, "") or "").strip()
            if v:
                out[k] = v
        path = OutputSettings._config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
        return out

    @staticmethod
    def download_folder() -> str:
        return OutputSettings.load()["download_folder"]

    @staticmethod
    def export_folder() -> str:
        return OutputSettings.load()["export_folder"]
