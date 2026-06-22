"""Test CRUD Project (SPEC 04 §2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import OWNER_HEADERS


def test_project_crud(client: TestClient) -> None:
    # Create
    r = client.post("/api/v1/projects", json={"name": "Kênh review"}, headers=OWNER_HEADERS)
    assert r.status_code == 201
    project = r.json()
    assert project["id"].startswith("proj_")
    assert project["name"] == "Kênh review"
    pid = project["id"]

    # Get
    r = client.get(f"/api/v1/projects/{pid}", headers=OWNER_HEADERS)
    assert r.status_code == 200

    # List
    r = client.get("/api/v1/projects", headers=OWNER_HEADERS)
    assert r.status_code == 200
    body = r.json()
    assert any(p["id"] == pid for p in body["items"])

    # Update
    r = client.patch(
        f"/api/v1/projects/{pid}", json={"description": "mô tả"}, headers=OWNER_HEADERS
    )
    assert r.status_code == 200
    assert r.json()["description"] == "mô tả"

    # Delete
    r = client.delete(f"/api/v1/projects/{pid}", headers=OWNER_HEADERS)
    assert r.status_code == 204

    # Get sau khi xoá -> 404
    r = client.get(f"/api/v1/projects/{pid}", headers=OWNER_HEADERS)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_create_validation_error(client: TestClient) -> None:
    r = client.post("/api/v1/projects", json={"name": ""}, headers=OWNER_HEADERS)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
