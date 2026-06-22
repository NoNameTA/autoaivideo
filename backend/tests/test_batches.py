"""Test tạo Batch -> Job -> Step và vòng đời job (SPEC 01 §6, 04 §2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import OWNER_HEADERS

EXPECTED_STEPS = 6  # faceless_v1 (SPEC 02 §4)


def _new_project(client: TestClient) -> str:
    r = client.post("/api/v1/projects", json={"name": "P"}, headers=OWNER_HEADERS)
    return r.json()["id"]


def test_create_batch_generates_jobs_and_steps(client: TestClient) -> None:
    pid = _new_project(client)
    payload = {"name": "Lô 1", "inputs": [{"topic": "A"}, {"topic": "B"}, {"topic": "C"}]}
    r = client.post(f"/api/v1/projects/{pid}/batches", json=payload, headers=OWNER_HEADERS)
    assert r.status_code == 201
    batch = r.json()
    assert batch["input_count"] == 3
    assert batch["counts"]["queued"] == 3
    bid = batch["id"]

    # 3 job được tạo
    r = client.get(f"/api/v1/batches/{bid}/jobs", headers=OWNER_HEADERS)
    assert r.status_code == 200
    jobs = r.json()["items"]
    assert len(jobs) == 3

    # Mỗi job có 6 step
    job_id = jobs[0]["id"]
    r = client.get(f"/api/v1/jobs/{job_id}", headers=OWNER_HEADERS)
    assert r.status_code == 200
    detail = r.json()
    assert len(detail["steps"]) == EXPECTED_STEPS
    assert detail["steps"][0]["step_key"] == "script"


def test_cancel_job(client: TestClient) -> None:
    pid = _new_project(client)
    r = client.post(
        f"/api/v1/projects/{pid}/batches",
        json={"name": "L", "inputs": [{"x": 1}]},
        headers=OWNER_HEADERS,
    )
    bid = r.json()["id"]
    job_id = client.get(f"/api/v1/batches/{bid}/jobs", headers=OWNER_HEADERS).json()["items"][0][
        "id"
    ]

    r = client.post(f"/api/v1/jobs/{job_id}/cancel", headers=OWNER_HEADERS)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


def test_retry_requires_failed(client: TestClient) -> None:
    pid = _new_project(client)
    r = client.post(
        f"/api/v1/projects/{pid}/batches",
        json={"name": "L", "inputs": [{"x": 1}]},
        headers=OWNER_HEADERS,
    )
    bid = r.json()["id"]
    job_id = client.get(f"/api/v1/batches/{bid}/jobs", headers=OWNER_HEADERS).json()["items"][0][
        "id"
    ]
    # Job đang queued -> retry phải 409
    r = client.post(f"/api/v1/jobs/{job_id}/retry", headers=OWNER_HEADERS)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


def test_idempotency_key(client: TestClient) -> None:
    pid = _new_project(client)
    headers = {**OWNER_HEADERS, "Idempotency-Key": "abc-123"}
    body = {"name": "L", "inputs": [{"x": 1}]}
    r1 = client.post(f"/api/v1/projects/{pid}/batches", json=body, headers=headers)
    r2 = client.post(f"/api/v1/projects/{pid}/batches", json=body, headers=headers)
    assert r1.status_code == 201
    assert r2.json()["id"] == r1.json()["id"]


def test_create_batch_unknown_project(client: TestClient) -> None:
    r = client.post(
        "/api/v1/projects/proj_khongco/batches",
        json={"name": "L", "inputs": [{"x": 1}]},
        headers=OWNER_HEADERS,
    )
    assert r.status_code == 404
