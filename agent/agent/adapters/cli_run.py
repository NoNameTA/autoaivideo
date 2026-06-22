"""Adapter `cli.run` — chạy lệnh cục bộ thật, thu file output thành asset (SPEC 06, 08).

config.command = argv (list). Biến của job được truyền qua env STEP_INPUTS (JSON) để lệnh dùng.
"""

from __future__ import annotations

import json
import os

from agent.config import AgentSettings
from agent.drivers import process
from agent.fs import collect_assets, step_output_dir


class CliRunAdapter:
    capability = "cli.run"

    async def run(self, settings: AgentSettings, data: dict) -> list[dict]:
        step_id = data["step_id"]
        job_id = data["job_id"]
        config = data.get("config", {}) or {}
        inputs = data.get("inputs", {}) or {}

        command = config.get("command")
        if not isinstance(command, list) or not command:
            raise RuntimeError("config.command phải là danh sách argv không rỗng")

        out_dir = step_output_dir(settings.data_dir, job_id, step_id)
        env = {**os.environ, "STEP_INPUTS": json.dumps(inputs, ensure_ascii=False)}

        result = await process.run(command, str(out_dir), env, settings.step_timeout)
        if result.code != 0:
            raise RuntimeError(f"Lệnh lỗi (rc={result.code}): {result.stderr[:500]}")

        return collect_assets(settings.data_dir, out_dir)
