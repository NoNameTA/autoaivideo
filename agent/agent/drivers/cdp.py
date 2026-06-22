"""CDP Driver (SPEC 05 §4, 08 §5) — điều khiển Chromium/Edge headless qua DevTools Protocol.

Hiện thực bằng raw CDP (websockets + httpx) thay cho Playwright (nhẹ, không tải browser riêng),
giữ đúng API §5: goto / eval / wait_for / click / type / screenshot / title / close.
"""

from __future__ import annotations

import asyncio
import base64
import json
import shutil
import socket
import tempfile
from pathlib import Path

import httpx
import websockets

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]
EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser(kind: str, override: str | None = None) -> str | None:
    if override:
        return override
    candidates = EDGE_CANDIDATES if kind == "edge" else CHROME_CANDIDATES
    for path in candidates:
        if Path(path).exists():
            return path
    exe = "msedge" if kind == "edge" else "chrome"
    return shutil.which(exe) or shutil.which(f"{exe}.exe")


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class CdpError(Exception):
    pass


class CdpDriver:
    def __init__(self, browser_path: str, *, headless: bool = True) -> None:
        self._browser = browser_path
        self._headless = headless
        self._proc: asyncio.subprocess.Process | None = None
        self._ws = None
        self._profile: Path | None = None
        self._id = 0

    async def launch(self) -> CdpDriver:
        port = _free_port()
        self._profile = Path(tempfile.mkdtemp(prefix="aivideo_cdp_"))
        args = [
            self._browser,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={self._profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "about:blank",
        ]
        if self._headless:
            args.insert(1, "--headless=new")
        self._proc = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
        )
        ws_url = await self._wait_target(port, timeout=20)
        self._ws = await websockets.connect(ws_url, max_size=None)
        await self._call("Page.enable", {})
        await self._call("Runtime.enable", {})
        return self

    async def _wait_target(self, port: int, timeout: float) -> str:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        async with httpx.AsyncClient() as client:
            while loop.time() < deadline:
                try:
                    resp = await client.get(f"http://127.0.0.1:{port}/json")
                    for t in resp.json():
                        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                            return t["webSocketDebuggerUrl"]
                except Exception:  # noqa: BLE001 - browser đang khởi động
                    pass
                await asyncio.sleep(0.3)
        raise CdpError("CDP không sẵn sàng (timeout)")

    async def _call(self, method: str, params: dict) -> dict:
        self._id += 1
        msg_id = self._id
        await self._ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
        while True:
            data = json.loads(await self._ws.recv())
            if data.get("id") == msg_id:
                if "error" in data:
                    raise CdpError(str(data["error"]))
                return data.get("result", {})

    async def eval(self, expression: str):
        result = await self._call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        if result.get("exceptionDetails"):
            raise CdpError(str(result["exceptionDetails"].get("text", "eval error")))
        return result.get("result", {}).get("value")

    async def goto(self, url: str, timeout: float = 15) -> None:
        await self._call("Page.navigate", {"url": url})
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        while loop.time() < deadline:
            if await self.eval("document.readyState === 'complete'"):
                return
            await asyncio.sleep(0.2)

    async def wait_for(self, selector: str, timeout: float = 10) -> None:
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        sel = json.dumps(selector)
        while loop.time() < deadline:
            if await self.eval(f"!!document.querySelector({sel})"):
                return
            await asyncio.sleep(0.2)
        raise CdpError(f"wait_for hết hạn: {selector}")

    async def click(self, selector: str) -> None:
        sel = json.dumps(selector)
        await self.eval(
            f"(()=>{{const e=document.querySelector({sel});"
            f"if(!e) throw new Error('no element'); e.click(); return true;}})()"
        )

    async def type(self, selector: str, text: str) -> None:
        sel = json.dumps(selector)
        val = json.dumps(text)
        await self.eval(
            f"(()=>{{const e=document.querySelector({sel});"
            f"if(!e) throw new Error('no element'); e.focus(); e.value={val};"
            f"e.dispatchEvent(new Event('input',{{bubbles:true}})); return e.value;}})()"
        )

    async def title(self) -> str:
        return await self.eval("document.title")

    async def screenshot(self) -> bytes:
        result = await self._call("Page.captureScreenshot", {"format": "png"})
        return base64.b64decode(result["data"])

    async def close(self) -> None:
        try:
            if self._ws:
                await self._ws.close()
        finally:
            if self._proc:
                self._proc.terminate()
                try:
                    await asyncio.wait_for(self._proc.wait(), timeout=5)
                except TimeoutError:
                    self._proc.kill()
            if self._profile:
                shutil.rmtree(self._profile, ignore_errors=True)
