"""UI Automation Driver (SPEC 05 §4, 08 §5) — pywinauto điều khiển app desktop Windows.

API: start / focus_window / type_keys / get_text / close. Kết nối cửa sổ theo title qua Desktop
(một số app như Notepad Win11 bàn giao cửa sổ sang process khác). Windows-only; import pywinauto
ở mức hàm để module vẫn nạp được khi kiểm thử ngoài Windows.
"""

from __future__ import annotations

import os
import signal
import time
from typing import Any


class UiaError(Exception):
    pass


class UiaDriver:
    def __init__(self) -> None:
        self._app: Any = None
        self._win: Any = None

    def start(self, path: str, title_re: str | None = None, timeout: float = 15) -> UiaDriver:
        try:
            from pywinauto import Application, Desktop
        except ImportError:
            raise UiaError("pywinauto chưa sẵn sàng (Windows-only)") from None

        self._app = Application(backend="uia").start(path)
        if title_re is None:
            self._win = self._app.top_window()
            self._win.wait("visible ready", timeout=timeout)
            return self

        deadline = time.time() + timeout
        last_err: Exception | None = None
        while time.time() < deadline:
            try:
                win = Desktop(backend="uia").window(title_re=title_re)
                if win.exists(timeout=1):
                    win.wait("visible ready", timeout=3)
                    self._win = win
                    return self
            except Exception as e:  # noqa: BLE001 - cửa sổ đang mở
                last_err = e
            time.sleep(0.5)
        raise UiaError(f"Không tìm thấy cửa sổ '{title_re}': {last_err}")

    def focus_window(self) -> None:
        self._win.set_focus()

    def type_keys(self, text: str) -> None:
        self._win.type_keys(text, with_spaces=True, with_newlines=True)

    def get_text(self) -> str:
        for control_type in ("Document", "Edit"):
            try:
                ctrl = self._win.child_window(control_type=control_type)
                if ctrl.exists(timeout=1):
                    value = ctrl.window_text()
                    if value:
                        return value
                    getter = getattr(ctrl, "get_value", None)
                    if callable(getter):
                        return getter()
            except Exception:  # noqa: BLE001 - thử control kế tiếp
                continue
        return self._win.window_text()

    def close(self) -> None:
        pid = None
        try:
            pid = self._win.process_id() if self._win is not None else None
        except Exception:  # noqa: BLE001
            pid = None
        try:
            if self._app is not None:
                self._app.kill()
        except Exception:  # noqa: BLE001
            pass
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)  # TerminateProcess trên Windows (không hỏi Save)
            except OSError:
                pass
