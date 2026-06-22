"""Quản lý kết nối WebSocket dashboard + broadcast theo subscription (SPEC 09 §2, §3)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import WebSocket

from app.db.ids import new_id


def envelope(type_: str, data: dict[str, Any], trace_id: str | None = None) -> dict:
    return {
        "v": 1,
        "type": type_,
        "id": new_id("msg"),
        "ts": datetime.now(UTC).isoformat(),
        "trace_id": trace_id,
        "data": data,
    }


class ConnectionManager:
    def __init__(self) -> None:
        self._subs: dict[WebSocket, set[str]] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._subs[ws] = set()

    def disconnect(self, ws: WebSocket) -> None:
        self._subs.pop(ws, None)

    def subscribe(self, ws: WebSocket, scope: str, id_: str) -> None:
        self._subs.setdefault(ws, set()).add(f"{scope}:{id_}")

    def unsubscribe(self, ws: WebSocket, scope: str, id_: str) -> None:
        self._subs.get(ws, set()).discard(f"{scope}:{id_}")

    async def broadcast(
        self,
        type_: str,
        data: dict[str, Any],
        *,
        scope: str | None = None,
        id_: str | None = None,
    ) -> None:
        """Gửi tới tất cả client; nếu có scope/id thì chỉ client đã subscribe kênh đó."""
        message = envelope(type_, data)
        target = f"{scope}:{id_}" if scope and id_ else None
        for ws, subs in list(self._subs.items()):
            if target is not None and target not in subs:
                continue
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 - client rớt giữa chừng
                self.disconnect(ws)


manager = ConnectionManager()
