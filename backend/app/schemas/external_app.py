from __future__ import annotations

from pydantic import BaseModel


class ConnectionStatus(BaseModel):
    status: str  # connected | no_agent | disabled
    online_agents: list[str]
    capacity_free: bool


class ExternalAppOut(BaseModel):
    """App ngoài (adapter/plugin) ở góc nhìn vận hành (SPEC 06)."""

    name: str
    capability: str
    type: str
    version: str
    enabled: bool
    free: bool
    license: str | None
    source_url: str | None
    connection: ConnectionStatus


class ExternalAppTestResult(BaseModel):
    ok: bool
    reason: str
    agents: list[str]
