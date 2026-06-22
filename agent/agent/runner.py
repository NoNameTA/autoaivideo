"""Điều phối step tới adapter theo capability (SPEC 05 §5)."""

from __future__ import annotations

from agent.adapters.cli_run import CliRunAdapter
from agent.config import AgentSettings

# Đăng ký adapter agent thật sự hiện thực được (capability -> adapter).
ADAPTERS: dict[str, type] = {CliRunAdapter.capability: CliRunAdapter}


def capabilities() -> list[str]:
    return sorted(ADAPTERS.keys())


async def run_step(settings: AgentSettings, data: dict) -> list[dict]:
    capability = data.get("adapter") or data.get("capability")
    adapter_cls = ADAPTERS.get(capability)
    if adapter_cls is None:
        raise RuntimeError(f"Agent không hỗ trợ adapter '{capability}'")
    return await adapter_cls().run(settings, data)
