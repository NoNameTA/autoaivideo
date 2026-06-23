"""Test trang External Apps (SPEC 06): liệt kê + trạng thái kết nối + test kết nối."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.orchestrator.agent_registry import AgentConn, registry
from tests.conftest import OWNER_HEADERS

_CAP = "cap.myapp"


def _register(client: TestClient) -> None:
    client.post(
        "/api/v1/plugins",
        json={
            "name": "myapp",
            "version": "1.0.0",
            "capability": _CAP,
            "type": "cli-process",
            "manifest": {"free": True, "license": "MIT", "source_url": "https://example.com"},
        },
        headers=OWNER_HEADERS,
    )


def _find(apps: list[dict], name: str) -> dict:
    return next(a for a in apps if a["name"] == name)


def test_list_external_apps(client: TestClient) -> None:
    _register(client)
    apps = client.get("/api/v1/external-apps", headers=OWNER_HEADERS).json()
    app = _find(apps, "myapp")
    assert app["capability"] == _CAP
    assert app["type"] == "cli-process"
    assert app["free"] is True
    assert app["license"] == "MIT"
    assert app["source_url"] == "https://example.com"
    # Chưa bật -> disabled.
    assert app["connection"]["status"] == "disabled"

    # Bật -> chưa có agent -> no_agent.
    client.patch("/api/v1/plugins/myapp", json={"enabled": True}, headers=OWNER_HEADERS)
    app2 = _find(client.get("/api/v1/external-apps", headers=OWNER_HEADERS).json(), "myapp")
    assert app2["connection"]["status"] == "no_agent"
    assert app2["connection"]["online_agents"] == []


def test_test_connection_disabled_then_no_agent(client: TestClient) -> None:
    _register(client)
    # Đang tắt.
    r = client.post("/api/v1/external-apps/myapp/test", headers=OWNER_HEADERS).json()
    assert r["ok"] is False
    assert "tắt" in r["reason"].lower()

    # Bật nhưng không có agent.
    client.patch("/api/v1/plugins/myapp", json={"enabled": True}, headers=OWNER_HEADERS)
    r2 = client.post("/api/v1/external-apps/myapp/test", headers=OWNER_HEADERS).json()
    assert r2["ok"] is False
    assert _CAP in r2["reason"]
    assert r2["agents"] == []


def test_test_connection_connected(client: TestClient) -> None:
    _register(client)
    client.patch("/api/v1/plugins/myapp", json={"enabled": True}, headers=OWNER_HEADERS)
    registry.add(AgentConn(agent_id="ag-test", ws=None, capabilities=[_CAP], capacity=2))
    try:
        r = client.post("/api/v1/external-apps/myapp/test", headers=OWNER_HEADERS).json()
        assert r["ok"] is True
        assert r["agents"] == ["ag-test"]
        assert _CAP in r["reason"]
        # Trạng thái kết nối trong list cũng "connected".
        app = _find(client.get("/api/v1/external-apps", headers=OWNER_HEADERS).json(), "myapp")
        assert app["connection"]["status"] == "connected"
        assert app["connection"]["capacity_free"] is True
    finally:
        registry.remove("ag-test")


def test_test_connection_not_found(client: TestClient) -> None:
    r = client.post("/api/v1/external-apps/khongco/test", headers=OWNER_HEADERS)
    assert r.status_code == 404
