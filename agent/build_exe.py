"""Đóng gói Desktop Agent thành .exe bằng PyInstaller (SPEC 13 §5).

Chạy:  python build_exe.py   ->  dist/aivideo-agent.exe

Plugin KHÔNG nhúng trong exe (nạp từ thư mục lúc chạy). Khi chạy exe, đặt biến môi trường
PLUGINS_DIR trỏ tới thư mục plugins/ (kèm các adapter app ngoài).
"""

from __future__ import annotations

import PyInstaller.__main__

if __name__ == "__main__":
    PyInstaller.__main__.run(
        [
            "run.py",
            "--onefile",
            "--name",
            "aivideo-agent",
            "--collect-all",
            "watchdog",
            "--hidden-import",
            "httpx",
            "--hidden-import",
            "yaml",
            "--noconfirm",
            "--clean",
        ]
    )
