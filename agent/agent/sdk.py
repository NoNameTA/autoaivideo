"""Plugin SDK (SPEC 08): interface Adapter + lifecycle + StepContext + driver + lỗi phân loại.

Adapter chạy phía agent, điều khiển app ngoài. Vòng đời: validate_config -> prepare -> run
-> collect -> cleanup. Plugin trong thư mục plugins/<name>/ import từ `agent.sdk`.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

from agent.drivers import process
from agent.drivers.process import ProcessResult
from agent.fs import collect_assets

SDK_VERSION = "1.0.0"


class TransientError(Exception):
    """Lỗi tạm thời -> engine sẽ retry (SPEC 08 §6)."""


class PermanentError(Exception):
    """Lỗi vĩnh viễn -> fail ngay (SPEC 08 §6)."""


class Asset(TypedDict):
    kind: str
    path: str
    mime: str | None
    size: int
    checksum: str


class ProcessDriver:
    """Driver `process` (SPEC 08 §5) — chạy tiến trình trong thư mục output của step."""

    def __init__(self, cwd: Path, env: dict[str, str]) -> None:
        self._cwd = cwd
        self._env = env

    async def run(self, command: list[str], timeout: int) -> ProcessResult:
        return await process.run(command, str(self._cwd), self._env, timeout)


@dataclass
class StepContext:
    step_id: str
    job_id: str
    inputs: dict
    config: dict
    output_dir: Path
    process: ProcessDriver
    data_dir: str
    timeout: int
    trace_id: str | None = None
    # Capability đang chạy (cloud-api: 1 adapter phục vụ nhiều capability, SPEC 06 §9.6).
    capability: str = ""
    on_progress: Callable[[int, str], None] | None = field(default=None, repr=False)
    # Resolver credential JIT (SPEC 11 §3.3): nhận payload -> trả material (token ngắn hạn).
    credential_resolver: Callable[[dict], Awaitable[dict]] | None = field(
        default=None, repr=False
    )

    def progress(self, pct: int, msg: str = "") -> None:
        if self.on_progress:
            self.on_progress(pct, msg)

    async def get_credential(self, operation: str = "", scopes: list[str] | None = None) -> dict:
        """Xin token ngắn hạn từ Backend (JIT). Material chỉ ở RAM, KHÔNG cache/log/ghi file."""
        if self.credential_resolver is None:
            raise PermanentError("Không có kênh credential (step không chạy qua agent online?)")
        ref = self.config.get("credential_ref")
        conn = self.config.get("connection_id")
        if not ref and not conn:
            raise PermanentError("Step thiếu credential_ref/connection_id")
        payload = {
            "step_id": self.step_id,
            "credential_ref": ref,
            "connection_id": conn,
            "operation": operation or self.capability,
            "scopes": scopes,
        }
        material = await self.credential_resolver(payload)
        if not material or not material.get("token"):
            raise PermanentError("Backend không cấp được credential")
        return material

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger("adapter")


class Adapter(ABC):
    """Lớp cơ sở cho mọi adapter. `capability` phải khớp manifest.

    Adapter cloud-api có thể phục vụ NHIỀU capability: khai `capabilities` (list) và đọc
    `ctx.capability` trong run() để biết operation (SPEC 06 §9.6).
    """

    capability: str = ""
    capabilities: list[str] = []
    requires_sdk: str = "1.0.0"

    def validate_config(self, config: dict) -> None:  # noqa: B027 - hook tuỳ chọn
        """Kiểm tra config (đã được JSON Schema check sơ bộ). Raise nếu sai."""

    async def prepare(self, ctx: StepContext) -> None:  # noqa: B027 - hook tuỳ chọn
        """Mở app / healthcheck. Mặc định no-op."""

    @abstractmethod
    async def run(self, ctx: StepContext) -> None:
        """Thực hiện công việc chính."""

    async def collect(self, ctx: StepContext) -> list[Asset]:
        """Thu file kết quả trong output_dir thành asset (mặc định quét toàn bộ)."""
        return collect_assets(ctx.data_dir, ctx.output_dir)  # type: ignore[return-value]

    async def cleanup(self, ctx: StepContext) -> None:  # noqa: B027 - hook tuỳ chọn
        """Dọn tài nguyên. Mặc định no-op."""


def build_step_inputs_env(inputs: dict) -> dict[str, str]:
    return {**os.environ, "STEP_INPUTS": json.dumps(inputs, ensure_ascii=False)}
