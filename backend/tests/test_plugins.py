"""Test registry Plugin (SPEC 04 §2, 08)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import OWNER_HEADERS


def test_plugin_lifecycle(client: TestClient) -> None:
    payload = {
        "name": "ffmpeg",
        "version": "1.0.0",
        "capability": "video.ffmpeg",
        "type": "cli-process",
        "manifest": {
            "config_schema": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
            }
        },
    }
    r = client.post("/api/v1/plugins", json=payload, headers=OWNER_HEADERS)
    assert r.status_code == 201
    assert r.json()["enabled"] is False

    # List
    r = client.get("/api/v1/plugins", headers=OWNER_HEADERS)
    assert any(p["name"] == "ffmpeg" for p in r.json())

    # Schema
    r = client.get("/api/v1/plugins/ffmpeg/schema", headers=OWNER_HEADERS)
    assert r.status_code == 200
    assert r.json()["schema"]["type"] == "object"

    # Enable
    r = client.patch("/api/v1/plugins/ffmpeg", json={"enabled": True}, headers=OWNER_HEADERS)
    assert r.json()["enabled"] is True

    # Remove
    r = client.delete("/api/v1/plugins/ffmpeg", headers=OWNER_HEADERS)
    assert r.status_code == 204
    r = client.get("/api/v1/plugins/ffmpeg/schema", headers=OWNER_HEADERS)
    assert r.status_code == 404
