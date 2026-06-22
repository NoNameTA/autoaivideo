"""Test WebSocket dashboard (SPEC 09 §3)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


def test_ws_requires_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/ws?token=sai"):
            pass


def test_ws_subscribe_ok(client: TestClient) -> None:
    with client.websocket_connect("/ws?token=change-me-owner-token") as ws:
        ws.send_json({"v": 1, "type": "subscribe", "data": {"scope": "batch", "id": "batch_x"}})
        # Không lỗi là đạt; gửi unsubscribe rồi đóng.
        ws.send_json({"v": 1, "type": "unsubscribe", "data": {"scope": "batch", "id": "batch_x"}})
