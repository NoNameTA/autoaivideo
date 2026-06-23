"""Test list job toàn cục cho trang Queue (SPEC 04 §2)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import OWNER_HEADERS


def _batch_with_jobs(client: TestClient, n: int) -> str:
    pid = client.post("/api/v1/projects", json={"name": "P"}, headers=OWNER_HEADERS).json()["id"]
    inputs = [{"k": i} for i in range(n)]
    r = client.post(
        f"/api/v1/projects/{pid}/batches",
        json={"name": "B", "inputs": inputs},
        headers=OWNER_HEADERS,
    )
    return r.json()["id"]


def test_list_jobs_global(client: TestClient) -> None:
    _batch_with_jobs(client, 3)
    r = client.get("/api/v1/jobs", headers=OWNER_HEADERS)
    assert r.status_code == 200
    jobs = r.json()
    assert len(jobs) >= 3
    assert all(j["status"] == "queued" for j in jobs)


def test_list_jobs_filter_and_search(client: TestClient) -> None:
    batch_id = _batch_with_jobs(client, 2)
    assert len(client.get("/api/v1/jobs?status=queued", headers=OWNER_HEADERS).json()) >= 2
    assert client.get("/api/v1/jobs?status=completed", headers=OWNER_HEADERS).json() == []
    found = client.get(f"/api/v1/jobs?search={batch_id}", headers=OWNER_HEADERS).json()
    assert len(found) == 2
    assert all(j["batch_id"] == batch_id for j in found)
    assert client.get("/api/v1/jobs?search=khongcogi", headers=OWNER_HEADERS).json() == []
