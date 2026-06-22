"""WS client kết nối backend /ws/agent: register + heartbeat + nhận step.assign (SPEC 09 §4)."""

from __future__ import annotations

import asyncio
import json
import logging
import platform

import websockets

from agent import __version__
from agent.adapter_registry import capabilities
from agent.config import AgentSettings
from agent.runner import run_step
from agent.sdk import TransientError

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
            "capabilities": capabilities(),
            "capacity": settings.capacity,
            "os": platform.system().lower(),
        },
    )


async def _heartbeat_loop(ws, settings: AgentSettings) -> None:
    while True:
        await asyncio.sleep(settings.heartbeat_interval)
        await _send(ws, "heartbeat", {"agent_id": settings.agent_id, "load": 0})


async def _exec_step(ws, settings: AgentSettings, data: dict) -> None:
    step_id = data["step_id"]
    await _send(ws, "step.ack", {"step_id": step_id})
    try:
        assets = await run_step(settings, data)
        await _send(ws, "step.completed", {"step_id": step_id, "assets": assets})
        log.info("step %s hoàn tất (%d asset)", step_id, len(assets))
    except TransientError as e:
        await _send(ws, "step.failed", {"step_id": step_id, "error": str(e), "retryable": True})
        log.warning("step %s lỗi tạm thời: %s", step_id, e)
    except Exception as e:  # noqa: BLE001 - lỗi vĩnh viễn -> báo về backend
        await _send(ws, "step.failed", {"step_id": step_id, "error": str(e), "retryable": False})
        log.warning("step %s lỗi: %s", step_id, e)


async def _session(settings: AgentSettings) -> None:
    url = f"{settings.backend_ws_url}?token={settings.agent_token}"
    async with websockets.connect(url, max_size=None) as ws:
        await _register(ws, settings)
        log.info("Đã đăng ký agent %s (capabilities=%s)", settings.agent_id, capabilities())
        hb = asyncio.create_task(_heartbeat_loop(ws, settings))
        try:
            async for raw in ws:
                msg = json.loads(raw)
                if msg.get("type") == "step.assign":
                    asyncio.create_task(_exec_step(ws, settings, msg["data"]))
                elif msg.get("type") == "step.cancel":
                    log.info("Nhận step.cancel %s", msg["data"].get("step_id"))
        finally:
            hb.cancel()


async def run_agent(settings: AgentSettings) -> None:
    while True:
        try:
            await _session(settings)
        except Exception as e:  # noqa: BLE001 - tự kết nối lại
            log.warning("Mất kết nối WS (%s); thử lại sau 3s", e)
            await asyncio.sleep(3)
