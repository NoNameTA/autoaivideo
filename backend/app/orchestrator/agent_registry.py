"""Sổ đăng ký kết nối agent đang online (in-memory) để dispatcher gửi step.assign.

Trạng thái bền nằm ở bảng agents; đây chỉ là các socket đang mở (SPEC 05 §3, 04 §4).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AgentConn:
    agent_id: str
    ws: Any
    capabilities: list[str]
    capacity: int
    inflight: int = 0


class AgentRegistry:
    def __init__(self) -> None:
        self._conns: dict[str, AgentConn] = {}

    def add(self, conn: AgentConn) -> None:
        self._conns[conn.agent_id] = conn

    def remove(self, agent_id: str) -> None:
        self._conns.pop(agent_id, None)

    def get(self, agent_id: str) -> AgentConn | None:
        return self._conns.get(agent_id)

    def pick(self, adapter: str) -> AgentConn | None:
        for conn in self._conns.values():
            if adapter in conn.capabilities and conn.inflight < conn.capacity:
                return conn
        return None

    def dec_inflight(self, agent_id: str) -> None:
        conn = self._conns.get(agent_id)
        if conn and conn.inflight > 0:
            conn.inflight -= 1

    async def send(self, agent_id: str, message: dict) -> bool:
        conn = self._conns.get(agent_id)
        if not conn:
            return False
        try:
            await conn.ws.send_json(message)
            return True
        except Exception:  # noqa: BLE001 - socket rớt
            self.remove(agent_id)
            return False


registry = AgentRegistry()
