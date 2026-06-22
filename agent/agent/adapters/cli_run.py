"""Adapter built-in `cli.run` — chạy lệnh cục bộ thật (SPEC 06 cli-process, 08).

config.command = argv (list). Biến job truyền qua env STEP_INPUTS (JSON).
"""

from __future__ import annotations

from agent.sdk import Adapter, PermanentError, StepContext


class CliRunAdapter(Adapter):
    capability = "cli.run"

    def validate_config(self, config: dict) -> None:
        command = config.get("command")
        if not isinstance(command, list) or not command:
            raise PermanentError("config.command phải là danh sách argv không rỗng")

    async def run(self, ctx: StepContext) -> None:
        command = ctx.config["command"]
        result = await ctx.process.run(command, ctx.timeout)
        if result.code != 0:
            raise PermanentError(f"Lệnh lỗi (rc={result.code}): {result.stderr[:500]}")
