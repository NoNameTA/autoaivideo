"""Credential RPC phía Agent (SPEC 09 §4.3): xin credential JIT từ Backend qua /ws/agent.

Correlation theo request_id. Material trả về CHỈ giữ trong RAM lúc dùng (caller xoá sau op);
KHÔNG cache/log/ghi file (SPEC 11 §3.3).
"""
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from agent.sdk import PermanentError, TransientError

# send_fn(type_, data) gửi 1 message lên backend qua ws.
SendFn = Callable[[str, dict], Awaitable[None]]


class CredentialRpc:
    def __init__(self) -> None:
        self._pending: dict[str, asyncio.Future] = {}
        self._n = 0

    def resolve(
        self, request_id: str | None, ok: bool, material: dict | None, error: dict | None
    ) -> None:
        fut = self._pending.pop(request_id or "", None)
        if fut is None or fut.done():
            return
        if ok and material:
            fut.set_result(material)
        else:
            msg = (error or {}).get("message", "credential bị từ chối")
            code = (error or {}).get("code", "")
            exc = TransientError(msg) if code == "RATE_LIMITED" else PermanentError(msg)
            fut.set_exception(exc)

    async def request(self, send_fn: SendFn, payload: dict, timeout: int = 30) -> dict:
        self._n += 1
        req_id = f"cred-{self._n}"
        fut: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[req_id] = fut
        await send_fn("credential.request", {**payload, "request_id": req_id})
        try:
            return await asyncio.wait_for(fut, timeout)
        except TimeoutError:
            raise PermanentError("Hết thời gian chờ credential từ Backend") from None
        finally:
            self._pending.pop(req_id, None)
