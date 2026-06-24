"""WS client: register + heartbeat + step.assign + config.update + fs.request (SPEC 09 §4, 07)."""

from __future__ import annotations

import asyncio
import json
import logging
import platform

import websockets

from agent import __version__
from agent.adapter_registry import capabilities
from agent.cloud_rpc import CredentialRpc
from agent.config import AgentSettings
from agent.fs_manager import FsNotFound, FsOpError, FsPermissionError, fs_manager
from agent.runner import run_step
from agent.sdk import TransientError
from agent.watcher import FolderWatcher, event_key

log = logging.getLogger("agent")


async def _send(ws, type_: str, data: dict) -> None:
    await ws.send(json.dumps({"v": 1, "type": type_, "data": data}))


async def _register(ws, settings: AgentSettings) -> None:
    await _send(
        ws,
        "agent.register",
        {
            "agent_id": settings.agent_id,
            "version": __version__,
            "capabilities": capabilities(settings.plugins_dir or None),
            "capacity": settings.capacity,
            "os": platform.system().lower(),
        },
    )


async def _heartbeat_loop(ws, settings: AgentSettings) -> None:
    while True:
        await asyncio.sleep(settings.heartbeat_interval)
        await _send(ws, "heartbeat", {"agent_id": settings.agent_id, "load": 0})


async def _coalesce_loop(ws, queue: asyncio.Queue, debounce_ms: int) -> None:
    """Debounce/coalesce sự kiện watch: gộp trùng trong cửa sổ debounce rồi gửi (SPEC 07)."""
    debounce = max(debounce_ms, 0) / 1000
    while True:
        first = await queue.get()
        pending = {event_key(first): first}
        while True:
            try:
                nxt = await asyncio.wait_for(queue.get(), timeout=debounce)
            except TimeoutError:
                break
            pending[event_key(nxt)] = nxt
        for ev in pending.values():
            await _send(ws, "fs.event", ev)


async def _exec_step(ws, settings: AgentSettings, data: dict, cred_rpc: CredentialRpc) -> None:
    step_id = data["step_id"]
    await _send(ws, "step.ack", {"step_id": step_id})

    async def resolver(payload: dict) -> dict:
        return await cred_rpc.request(lambda t, d: _send(ws, t, d), payload)

    try:
        assets = await run_step(settings, data, resolver)
        await _send(ws, "step.completed", {"step_id": step_id, "assets": assets})
        log.info("step %s hoàn tất (%d asset)", step_id, len(assets))
    except TransientError as e:
        await _send(ws, "step.failed", {"step_id": step_id, "error": str(e), "retryable": True})
        log.warning("step %s lỗi tạm thời: %s", step_id, e)
    except Exception as e:  # noqa: BLE001 - lỗi vĩnh viễn -> báo về backend
        await _send(ws, "step.failed", {"step_id": step_id, "error": str(e), "retryable": False})
        log.warning("step %s lỗi: %s", step_id, e)


async def _handle_fs(ws, watcher: FolderWatcher, data: dict) -> None:
    req_id = data.get("request_id")
    op = data.get("op")
    params = data.get("params", {}) or {}
    try:
        if op == "watch":
            path = fs_manager.perm.check(params["path"])
            enable = bool(params.get("enable", True))
            watcher.request(path, enable)
            result = {"path": path, "watching": enable, "watched": watcher.watched}
        else:
            result = await fs_manager.handle(op, params)
        await _send(ws, "fs.response", {"request_id": req_id, "ok": True, "result": result})
    except (FsPermissionError, FsNotFound, FsOpError) as e:
        await _send(
            ws,
            "fs.response",
            {"request_id": req_id, "ok": False, "error": {"code": e.code, "message": str(e)}},
        )
    except Exception as e:  # noqa: BLE001
        await _send(
            ws,
            "fs.response",
            {"request_id": req_id, "ok": False, "error": {"code": "FS_ERROR", "message": str(e)}},
        )


async def _session(settings: AgentSettings) -> None:
    url = f"{settings.backend_ws_url}?token={settings.agent_token}"
    loop = asyncio.get_event_loop()
    async with websockets.connect(url, max_size=None) as ws:
        await _register(ws, settings)
        log.info(
            "Đã đăng ký agent %s (capabilities=%s)",
            settings.agent_id,
            capabilities(settings.plugins_dir or None),
        )

        queue: asyncio.Queue = asyncio.Queue()
        cred_rpc = CredentialRpc()

        def sink(ev: dict) -> None:
            # watchdog gọi từ thread khác -> đẩy về event loop.
            loop.call_soon_threadsafe(queue.put_nowait, ev)

        watcher = FolderWatcher(sink, fs_manager.perm.is_allowed)
        hb = asyncio.create_task(_heartbeat_loop(ws, settings))
        coalescer = asyncio.create_task(_coalesce_loop(ws, queue, settings.watch_debounce_ms))
        try:
            async for raw in ws:
                msg = json.loads(raw)
                mtype = msg.get("type")
                data = msg.get("data", {}) or {}
                if mtype == "step.assign":
                    asyncio.create_task(_exec_step(ws, settings, data, cred_rpc))
                elif mtype == "credential.response":
                    cred_rpc.resolve(
                        data.get("request_id"),
                        bool(data.get("ok")),
                        data.get("material"),
                        data.get("error"),
                    )
                elif mtype == "step.cancel":
                    log.info("Nhận step.cancel %s", data.get("step_id"))
                elif mtype == "config.update":
                    allowed = data.get("allowed_folders")
                    if allowed is not None:
                        fs_manager.perm.set_allowed(allowed)
                        # Tự reconcile watcher theo Allowed Folders mới (SPEC 07).
                        watcher.reconcile()
                        log.info("Allowed Folders=%s watch=%s", allowed, watcher.watched)
                elif mtype == "fs.request":
                    asyncio.create_task(_handle_fs(ws, watcher, data))
        finally:
            hb.cancel()
            coalescer.cancel()
            watcher.stop()


async def run_agent(settings: AgentSettings) -> None:
    while True:
        try:
            await _session(settings)
        except Exception as e:  # noqa: BLE001 - tự kết nối lại
            log.warning("Mất kết nối WS (%s); thử lại sau 3s", e)
            await asyncio.sleep(3)
