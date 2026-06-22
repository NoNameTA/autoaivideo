"""Adapter Edge (capability web.cdp.edge) — điều khiển Microsoft Edge headless qua CDP driver."""

from __future__ import annotations

import json

from agent.drivers.cdp import CdpDriver, find_browser
from agent.sdk import Adapter, PermanentError, StepContext

_BROWSER_KIND = "edge"


class EdgeCdpAdapter(Adapter):
    capability = "web.cdp.edge"

    async def run(self, ctx: StepContext) -> None:
        url = ctx.inputs.get("url") or ctx.config.get("url")
        if not url:
            raise PermanentError("Thiếu 'url' (inputs hoặc config)")
        browser = find_browser(_BROWSER_KIND, ctx.config.get("browser_path"))
        if not browser:
            raise PermanentError("Không tìm thấy Microsoft Edge")

        driver = CdpDriver(browser)
        try:
            await driver.launch()
            await driver.goto(url)
            title = await driver.title()
            png = await driver.screenshot()
            (ctx.output_dir / "screenshot.png").write_bytes(png)
            (ctx.output_dir / "page.json").write_text(
                json.dumps({"url": url, "title": title}, ensure_ascii=False), encoding="utf-8"
            )
        finally:
            await driver.close()
