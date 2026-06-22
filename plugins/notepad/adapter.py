"""Adapter Notepad (capability desktop.notepad) — minh hoạ UI Automation thật (SPEC 05 §4, 06 desktop-uia).

Mở Notepad bằng pywinauto, gõ văn bản thật, đọc lại nội dung, ghi thành asset. Không hard-code toạ độ.
"""

from __future__ import annotations

import asyncio

from agent.drivers.uia import UiaDriver, UiaError
from agent.sdk import Adapter, PermanentError, StepContext


class NotepadAdapter(Adapter):
    capability = "desktop.notepad"

    async def run(self, ctx: StepContext) -> None:
        text = str(ctx.inputs.get("text") or ctx.config.get("text") or "AI Video Platform")
        out = ctx.output_dir / "notepad.txt"

        def _drive() -> str:
            driver = UiaDriver()
            try:
                driver.start("notepad.exe", title_re="Notepad")
                driver.focus_window()
                driver.type_keys(text)
                return driver.get_text()
            finally:
                driver.close()

        try:
            read_back = await asyncio.to_thread(_drive)
        except UiaError as e:
            raise PermanentError(str(e)) from None

        out.write_text(read_back or text, encoding="utf-8")
