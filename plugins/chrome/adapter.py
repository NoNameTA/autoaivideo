"""Adapter Chrome CDP (capability web.cdp) — điều khiển Chrome headless qua DevTools Protocol.

Mở Chrome headless với --remote-debugging-port (kỹ thuật CDP, SPEC 05 §4), điều hướng URL và
chụp screenshot thật vào thư mục output. Không hard-code toạ độ chuột (SPEC 06).
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

from agent.sdk import Adapter, PermanentError, StepContext

_CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]


def _find_chrome(config: dict) -> str | None:
    if config.get("chrome_path"):
        return config["chrome_path"]
    for path in _CHROME_CANDIDATES:
        if Path(path).exists():
            return path
    return shutil.which("chrome") or shutil.which("chrome.exe")


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def _wait_debugger_ws(port: int, timeout: float) -> str:
    loop = asyncio.get_event_loop()
    deadline = loop.time() + timeout
    async with httpx.AsyncClient() as client:
        while loop.time() < deadline:
            try:
                resp = await client.get(f"http://127.0.0.1:{port}/json")
                for target in resp.json():
                    if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                        return target["webSocketDebuggerUrl"]
            except Exception:  # noqa: BLE001 - chrome đang khởi động
                pass
            await asyncio.sleep(0.3)
    raise PermanentError("Chrome CDP không sẵn sàng trong thời gian chờ")


async def _cdp_call(ws, msg_id: int, method: str, params: dict) -> dict:
    await ws.send(json.dumps({"id": msg_id, "method": method, "params": params}))
    while True:
        msg = json.loads(await ws.recv())
        if msg.get("id") == msg_id:
            return msg


class ChromeCdpAdapter(Adapter):
    capability = "web.cdp"

    async def run(self, ctx: StepContext) -> None:
        url = ctx.inputs.get("url") or ctx.config.get("url")
        if not url:
            raise PermanentError("Thiếu 'url' (inputs hoặc config)")
        chrome = _find_chrome(ctx.config)
        if not chrome:
            raise PermanentError("Không tìm thấy Chrome")

        port = _free_port()
        profile = Path(tempfile.mkdtemp(prefix="aivideo_cdp_"))
        proc = await asyncio.create_subprocess_exec(
            chrome,
            "--headless=new",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "about:blank",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            ws_url = await _wait_debugger_ws(port, timeout=20)
            async with websockets.connect(ws_url, max_size=None) as ws:
                await _cdp_call(ws, 1, "Page.enable", {})
                await _cdp_call(ws, 2, "Page.navigate", {"url": url})
                await asyncio.sleep(ctx.config.get("wait_ms", 1500) / 1000)
                shot = await _cdp_call(ws, 3, "Page.captureScreenshot", {"format": "png"})
                data = shot.get("result", {}).get("data")
                if not data:
                    raise PermanentError("Không chụp được screenshot")
                (ctx.output_dir / "screenshot.png").write_bytes(base64.b64decode(data))
        finally:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except TimeoutError:
                proc.kill()
            shutil.rmtree(profile, ignore_errors=True)
