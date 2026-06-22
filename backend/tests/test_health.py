"""Test health endpoints (SPEC 15 §2)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_ready(client: TestClient) -> None:
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_info(client: TestClient) -> None:
    r = client.get("/api/v1/info")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "AI Video Platform V2"
    assert body["version"]
