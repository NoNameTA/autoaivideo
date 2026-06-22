"""RPC fs.request/fs.response qua /ws/agent (SPEC 07, mở rộng 09 §4).

Backend gửi fs.request có request_id, chờ Future; ws/agent gọi resolve() khi nhận fs.response.
"""

from __future__ import annotations

import asyncio

from app.api.ws.manager import envelope
from app.core.errors import AgentUnavailableError, FsError
from app.db.ids import new_id
from app.orchestrator.agent_registry import registry

_DEFAULT_TIMEOUT = 30


class FsRpc:
    def __init__(self) -> None:
        self._pending: dict[str, asyncio.Future] = {}

    async def call(self, agent_id: str, op: str, params: dict, timeout: int = _DEFAULT_TIMEOUT):
        request_id = new_id("fsreq")
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        sent = await registry.send(
            agent_id, envelope("fs.request", {"request_id": request_id, "op": op, "params": params})
        )
        if not sent:
            self._pending.pop(request_id, None)
            raise AgentUnavailableError("Không gửi được lệnh tới agent")
        try:
            return await asyncio.wait_for(future, timeout)
        except TimeoutError:
            raise FsError("Agent không phản hồi (timeout)") from None
        finally:
            self._pending.pop(request_id, None)

    def resolve(self, request_id: str, ok: bool, result, error: dict | None) -> None:
        future = self._pending.get(request_id)
        if future is None or future.done():
            return
        if ok:
            future.set_result(result)
            return
        err = error or {}
        exc = FsError(err.get("message", "Lỗi thao tác file"))
        code = err.get("code")
        if code == "FORBIDDEN":
            exc.code, exc.status = "FORBIDDEN", 403
        elif code == "NOT_FOUND":
            exc.code, exc.status = "NOT_FOUND", 404
        future.set_exception(exc)


fs_rpc = FsRpc()
