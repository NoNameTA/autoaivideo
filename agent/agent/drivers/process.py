"""Process driver — chạy tiến trình cục bộ thật (SPEC 08 driver `process`, 06 cli-process)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class ProcessResult:
    code: int
    stdout: str
    stderr: str


async def run(
    command: list[str], cwd: str, env: dict[str, str], timeout: int
) -> ProcessResult:
    proc = await asyncio.create_subprocess_exec(
        *command,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError("Quá thời gian thực thi tiến trình") from None
    return ProcessResult(
        proc.returncode or 0,
        out.decode(errors="replace"),
        err.decode(errors="replace"),
    )
