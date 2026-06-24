"""Điều phối step tới adapter theo capability + chạy đúng lifecycle SDK (SPEC 05 §5, 08 §4)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from agent.adapter_registry import get_adapters
from agent.config import AgentSettings
from agent.fs import step_output_dir
from agent.sdk import PermanentError, ProcessDriver, StepContext, build_step_inputs_env


async def run_step(
    settings: AgentSettings,
    data: dict,
    credential_resolver: Callable[[dict], Awaitable[dict]] | None = None,
) -> list[dict]:
    capability = data.get("adapter") or data.get("capability")
    adapter = get_adapters(settings.plugins_dir or None).get(capability)
    if adapter is None:
        raise PermanentError(f"Agent không hỗ trợ adapter '{capability}'")

    config = data.get("config", {}) or {}
    inputs = data.get("inputs", {}) or {}
    out_dir = step_output_dir(settings.data_dir, data["job_id"], data["step_id"])
    ctx = StepContext(
        step_id=data["step_id"],
        job_id=data["job_id"],
        inputs=inputs,
        config=config,
        output_dir=out_dir,
        process=ProcessDriver(out_dir, build_step_inputs_env(inputs)),
        data_dir=settings.data_dir,
        timeout=settings.step_timeout,
        trace_id=data.get("trace_id"),
        capability=capability,
        credential_resolver=credential_resolver,
    )

    adapter.validate_config(config)
    await adapter.prepare(ctx)
    try:
        await adapter.run(ctx)
        return await adapter.collect(ctx)  # type: ignore[return-value]
    finally:
        await adapter.cleanup(ctx)
