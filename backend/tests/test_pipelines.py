"""Test Pipeline (Workflow) CRUD + run (SPEC 02 §4)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import OWNER_HEADERS


def test_builtins_seeded_and_listed(client: TestClient) -> None:
    r = client.get("/api/v1/pipelines", headers=OWNER_HEADERS)
    assert r.status_code == 200
    names = {p["name"] for p in r.json()}
    # sync_builtins (lifespan) seed các template JSON
    assert {"local_demo", "ffmpeg_demo"} <= names


def test_pipeline_crud(client: TestClient) -> None:
    body = {
        "name": "my_flow",
        "description": "test",
        "steps": [
            {"step_key": "a", "adapter": "cli.run", "config": {"command": ["python", "-c", "1"]}},
            {"step_key": "b", "adapter": "video.ffmpeg", "config": {}},
        ],
    }
    r = client.post("/api/v1/pipelines", json=body, headers=OWNER_HEADERS)
    assert r.status_code == 201
    assert len(r.json()["steps"]) == 2
    assert r.json()["builtin"] is False

    # trùng tên -> 409
    assert client.post("/api/v1/pipelines", json=body, headers=OWNER_HEADERS).status_code == 409

    # update steps
    body2 = {"steps": [{"step_key": "only", "adapter": "cli.run", "config": {}}]}
    r = client.patch("/api/v1/pipelines/my_flow", json=body2, headers=OWNER_HEADERS)
    assert r.status_code == 200 and len(r.json()["steps"]) == 1

    # delete
    assert client.delete("/api/v1/pipelines/my_flow", headers=OWNER_HEADERS).status_code == 204
    assert client.get("/api/v1/pipelines/my_flow", headers=OWNER_HEADERS).status_code == 404


def test_create_validation(client: TestClient) -> None:
    # tên có dấu cách -> 422
    bad = {"name": "bad name", "steps": [{"step_key": "a", "adapter": "cli.run"}]}
    assert client.post("/api/v1/pipelines", json=bad, headers=OWNER_HEADERS).status_code == 422
    # 0 step -> 422
    bad2 = {"name": "empty", "steps": []}
    assert client.post("/api/v1/pipelines", json=bad2, headers=OWNER_HEADERS).status_code == 422


def test_run_pipeline_creates_batch(client: TestClient) -> None:
    proj = client.post("/api/v1/projects", json={"name": "P"}, headers=OWNER_HEADERS).json()
    body = {"project_id": proj["id"], "name": "Run X", "inputs": [{"k": 1}, {"k": 2}]}
    r = client.post("/api/v1/pipelines/local_demo/run", json=body, headers=OWNER_HEADERS)
    assert r.status_code == 201
    assert r.json()["input_count"] == 2

    jobs = client.get(f"/api/v1/batches/{r.json()['id']}/jobs", headers=OWNER_HEADERS).json()
    assert len(jobs["items"]) == 2
