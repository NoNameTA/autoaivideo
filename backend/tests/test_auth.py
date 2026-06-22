"""Test xác thực token (SPEC 11 §2, 09 §6)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import OWNER_HEADERS


def test_missing_token_unauthorized(client: TestClient) -> None:
    r = client.get("/api/v1/projects")
    assert r.status_code == 401
    body = r.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["trace_id"]


def test_wrong_token_unauthorized(client: TestClient) -> None:
    r = client.get("/api/v1/projects", headers={"Authorization": "Bearer sai"})
    assert r.status_code == 401


def test_valid_token_ok(client: TestClient) -> None:
    r = client.get("/api/v1/projects", headers=OWNER_HEADERS)
    assert r.status_code == 200
