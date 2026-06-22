"""WebSocket cho frontend `/ws` (SPEC 09 §3)."""

from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.ws.manager import manager
from app.core.config import get_settings
from app.core.errors import UnauthorizedError
from app.core.security import verify_owner_token

router = APIRouter()


@router.websocket("/ws")
async def ws_dashboard(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    try:
        verify_owner_token(token, get_settings())
    except UnauthorizedError:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")
            data = msg.get("data", {}) or {}
            if mtype == "subscribe" and "scope" in data and "id" in data:
                manager.subscribe(websocket, data["scope"], data["id"])
            elif mtype == "unsubscribe" and "scope" in data and "id" in data:
                manager.unsubscribe(websocket, data["scope"], data["id"])
            # "ack" và các loại khác: bỏ qua an toàn.
    except WebSocketDisconnect:
        manager.disconnect(websocket)
