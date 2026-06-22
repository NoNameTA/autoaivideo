"""E2E THẬT (gated RUN_E2E=1): Web→Backend→Queue→Workflow→Agent→Plugin→WS→Dashboard.

Khởi chạy backend + agent thật bằng subprocess, chạy pipeline `ffmpeg_demo` (plugin video.ffmpeg
tạo video thật), xác minh: job completed, asset thật, Dashboard nhận realtime job + plugin.runtime.
Không mock/fake. Chỉ chạy khi RUN_E2E=1 (cần ffmpeg trong PATH).
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest
import websockets

pytestmark = pytest.mark.e2e

REPO = Path(__file__).resolve().parents[3]
BACKEND = REPO / "backend"
AGENT = REPO / "agent"
PORT = 8010
BASE = f"http://127.0.0.1:{PORT}"
OWNER = {"Authorization": "Bearer change-me-owner-token", "Content-Type": "application/json"}


def _req(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, headers=OWNER, method=method)
    with urllib.request.urlopen(r, timeout=10) as resp:
        return None if resp.status == 204 else json.load(resp)


def _wait_health(timeout: int = 30) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.5)
    return False


async def _scenario(data_dir: str) -> dict:
    kinds: set[str] = set()
    url = f"ws://127.0.0.1:{PORT}/ws?token=change-me-owner-token"
    async with websockets.connect(url) as ws:
        await asyncio.sleep(0.3)
        await asyncio.to_thread(_req, "POST", "/api/v1/fs/allowed", {"path": data_dir})
        proj = await asyncio.to_thread(
            _req, "POST", "/api/v1/projects", {"name": "E2E", "default_pipeline": "ffmpeg_demo"}
        )
        batch = await asyncio.to_thread(
            _req,
            "POST",
            f"/api/v1/projects/{proj['id']}/batches",
            {"name": "B", "inputs": [{"x": 1}]},
        )
        status = None
        deadline = asyncio.get_event_loop().time() + 45
        while asyncio.get_event_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=2)
                msg = json.loads(raw)
                if msg.get("type") == "activity":
                    kinds.add(msg["data"].get("kind"))
            except TimeoutError:
                pass
            jobs = await asyncio.to_thread(_req, "GET", f"/api/v1/batches/{batch['id']}/jobs")
            sts = [j["status"] for j in jobs["items"]]
            if sts and all(s in ("completed", "failed") for s in sts):
                status = sts[0]
                break
        # Drain các activity còn lại (vd job.updated phát ngay sau khi step xong).
        drain_end = asyncio.get_event_loop().time() + 2
        while asyncio.get_event_loop().time() < drain_end:
            try:
                msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=1))
                if msg.get("type") == "activity":
                    kinds.add(msg["data"].get("kind"))
            except TimeoutError:
                break
    asset = any(f == "out.mp4" for _, _, files in os.walk(data_dir) for f in files)
    return {"status": status, "kinds": kinds, "asset": asset}


def test_full_pipeline_e2e() -> None:
    tmp = tempfile.mkdtemp(prefix="aivideo_e2e_")
    db = os.path.join(tmp, "e2e.db").replace("\\", "/")
    data_dir = os.path.join(tmp, "data")
    os.makedirs(data_dir, exist_ok=True)
    env = {
        **os.environ,
        "DATABASE_URL": f"sqlite+aiosqlite:///{db}",
        "DATA_DIR": data_dir,
        "AUTH_TOKEN": "change-me-owner-token",
        "AGENT_TOKEN": "change-me-agent-token",
    }
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND, env=env, check=True, capture_output=True,
    )
    backend = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "app.main:app",
            "--port", str(PORT), "--log-level", "warning",
        ],
        cwd=BACKEND, env=env,
    )
    agent = None
    try:
        assert _wait_health(), "backend không khởi động"
        agent_env = {
            **os.environ,
            "BACKEND_WS_URL": f"ws://127.0.0.1:{PORT}/ws/agent",
            "AGENT_TOKEN": "change-me-agent-token",
            "AGENT_ID": "e2e-agent",
            "DATA_DIR": data_dir,
        }
        agent = subprocess.Popen([sys.executable, "-m", "agent.main"], cwd=AGENT, env=agent_env)
        time.sleep(3)
        result = asyncio.run(_scenario(data_dir))
        assert result["status"] == "completed", result
        assert result["asset"], f"thiếu out.mp4: {result}"
        assert "plugin.runtime.started" in result["kinds"], result
        assert "plugin.runtime.finished" in result["kinds"], result
        assert "job.updated" in result["kinds"], result
    finally:
        if agent:
            agent.terminate()
        backend.terminate()
