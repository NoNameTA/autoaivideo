"""RPC cookie.request/cookie.response qua /ws/agent (Cookie Manager — test cookie THẬT trên Agent).

Backend gửi cookie.request (đường dẫn + hosts + test_url), chờ Future; ws/agent gọi resolve() khi
nhận cookie.response. Agent là nơi DUY NHẤT đọc nội dung cookie (đúng kiến trúc). Mirror FsRpc.
"""
from __future__ import annotations

import asyncio

from app.api.ws.manager import envelope
from app.core.errors import AgentUnavailableError, AppError
from app.db.ids import new_id
from app.orchestrator.agent_registry import registry

_DEFAULT_TIMEOUT = 75  # đủ cho live-probe yt-dlp (--simulate) nếu có test_url


class CookieRpc:
    def __init__(self) -> None:
        self._pending: dict[str, asyncio.Future] = {}

    async def call(self, agent_id: str, params: dict, timeout: int = _DEFAULT_TIMEOUT) -> dict:
        request_id = new_id("ckreq")
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[request_id] = future
        sent = await registry.send(
            agent_id, envelope("cookie.request", {"request_id": request_id, "params": params})
        )
        if not sent:
            self._pending.pop(request_id, None)
            raise AgentUnavailableError("Không gửi được lệnh test cookie tới agent")
        try:
            return await asyncio.wait_for(future, timeout)
        except TimeoutError:
            raise AgentUnavailableError("Agent không phản hồi test cookie (timeout)") from None
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
        exc = AppError(err.get("message", "Test cookie lỗi"))
        exc.code = "COOKIE_ERROR"
        future.set_exception(exc)


cookie_rpc = CookieRpc()
