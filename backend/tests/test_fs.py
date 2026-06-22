"""Test File Manager backend: Allowed Folders + Permission Manager (SPEC 07, 11 §5)."""

from __future__ import annotations

import os
import tempfile

from fastapi.testclient import TestClient

from app.services.allowed_folder_service import is_within_allowed
from tests.conftest import OWNER_HEADERS


def test_is_within_allowed() -> None:
    root = os.path.realpath(tempfile.gettempdir())
    assert is_within_allowed(os.path.join(root, "a", "b"), [root])
    assert is_within_allowed(root, [root])
    assert not is_within_allowed(os.path.join(root, "..", "x"), [root])


def test_allowed_folder_crud(client: TestClient) -> None:
    d = tempfile.mkdtemp()
    r = client.post("/api/v1/fs/allowed", json={"path": d, "label": "T"}, headers=OWNER_HEADERS)
    assert r.status_code == 201
    fid = r.json()["id"]

    r = client.get("/api/v1/fs/allowed", headers=OWNER_HEADERS)
    assert any(f["id"] == fid for f in r.json())

    r = client.delete(f"/api/v1/fs/allowed/{fid}", headers=OWNER_HEADERS)
    assert r.status_code == 204


def test_scan_without_agent_returns_503(client: TestClient) -> None:
    d = tempfile.mkdtemp()
    client.post("/api/v1/fs/allowed", json={"path": d}, headers=OWNER_HEADERS)
    r = client.post("/api/v1/fs/scan", json={"path": d}, headers=OWNER_HEADERS)
    assert r.status_code == 503
    assert r.json()["error"]["code"] == "AGENT_UNAVAILABLE"


def test_scan_outside_allowed_returns_403(client: TestClient) -> None:
    allowed = tempfile.mkdtemp()
    outside = tempfile.mkdtemp()
    client.post("/api/v1/fs/allowed", json={"path": allowed}, headers=OWNER_HEADERS)
    r = client.post("/api/v1/fs/scan", json={"path": outside}, headers=OWNER_HEADERS)
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"
