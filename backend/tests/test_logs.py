"""Test trang Logs: suy `level` từ loại event + persist + lọc (SPEC 04 §7, 10 §2)."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.services.event_service import EventService, level_for
from tests.conftest import OWNER_HEADERS


def test_level_for_mapping() -> None:
    # error
    assert level_for("plugin.runtime.failed") == "error"
    assert level_for("plugin.lifecycle.registration_failed") == "error"
    assert level_for("job.updated", {"status": "failed"}) == "error"
    # warn
    assert level_for("step.retrying") == "warn"
    assert level_for("plugin.lifecycle.disabled") == "warn"
    assert level_for("plugin.lifecycle.removed") == "warn"
    assert level_for("job.updated", {"status": "cancelled"}) == "warn"
    # debug (nhiễu)
    assert level_for("plugin.runtime.progress") == "debug"
    # info (mặc định)
    assert level_for("plugin.lifecycle.installed") == "info"
    assert level_for("job.updated", {"status": "running"}) == "info"


def _register_plugin(client: TestClient, name: str) -> None:
    client.post(
        "/api/v1/plugins",
        json={"name": name, "version": "1.0.0", "capability": f"cap.{name}", "type": "cli-process"},
        headers=OWNER_HEADERS,
    )


def test_logs_api_persist_and_filter(client: TestClient) -> None:
    _register_plugin(client, "alpha")  # plugin.lifecycle.installed -> info
    # disabled -> warn
    client.patch("/api/v1/plugins/alpha", json={"enabled": False}, headers=OWNER_HEADERS)

    logs = client.get("/api/v1/logs", headers=OWNER_HEADERS).json()
    assert len(logs) >= 2
    kinds = {row["type"]: row for row in logs}
    assert kinds["plugin.lifecycle.installed"]["level"] == "info"
    assert kinds["plugin.lifecycle.installed"]["category"] == "plugin"
    assert kinds["plugin.lifecycle.disabled"]["level"] == "warn"

    # Lọc theo level
    warns = client.get("/api/v1/logs?level=warn", headers=OWNER_HEADERS).json()
    assert all(r["level"] == "warn" for r in warns)
    assert any(r["type"] == "plugin.lifecycle.disabled" for r in warns)

    # Lọc theo category=plugin
    by_cat = client.get("/api/v1/logs?category=plugin", headers=OWNER_HEADERS).json()
    assert by_cat and all(r["category"] == "plugin" for r in by_cat)

    # Lọc theo plugin cụ thể (entity_id = tên plugin với lifecycle event)
    by_plugin = client.get("/api/v1/logs?plugin=alpha", headers=OWNER_HEADERS).json()
    assert by_plugin and all(r["entity_id"] == "alpha" for r in by_plugin)

    # Tìm kiếm
    found = client.get("/api/v1/logs?search=installed", headers=OWNER_HEADERS).json()
    assert any(r["type"] == "plugin.lifecycle.installed" for r in found)


def test_logs_filter_by_batch_and_project(client: TestClient) -> None:
    # Ghi event mang job/batch/project context, kiểm tra lọc json_extract.
    async def _seed() -> None:
        await EventService.record(
            entity_type="job", entity_id="job_1", type="job.updated",
            data={
                "job_id": "job_1", "batch_id": "bat_1",
                "project_id": "prj_1", "status": "completed",
            },
        )
        await EventService.record(
            entity_type="job", entity_id="job_2", type="job.updated",
            data={
                "job_id": "job_2", "batch_id": "bat_2",
                "project_id": "prj_2", "status": "failed",
            },
        )

    asyncio.run(_seed())

    only_b1 = client.get("/api/v1/logs?batch_id=bat_1", headers=OWNER_HEADERS).json()
    assert only_b1 and all(r["data"].get("batch_id") == "bat_1" for r in only_b1)

    only_p2 = client.get("/api/v1/logs?project_id=prj_2", headers=OWNER_HEADERS).json()
    assert only_p2 and all(r["data"].get("project_id") == "prj_2" for r in only_p2)
    assert any(r["level"] == "error" for r in only_p2)  # status=failed -> error


def test_logs_excludes_idempotency_events(client: TestClient) -> None:
    # Tạo batch kèm Idempotency-Key -> sinh 1 event nội bộ `idempotency_batch`.
    pid = client.post("/api/v1/projects", json={"name": "P"}, headers=OWNER_HEADERS).json()["id"]
    client.post(
        f"/api/v1/projects/{pid}/batches",
        json={"name": "B", "inputs": [{"k": 1}]},
        headers={**OWNER_HEADERS, "Idempotency-Key": "k-1"},
    )
    # Ghi thêm 1 event bình thường để chứng minh Logs vẫn hiển thị event thật.
    asyncio.run(
        EventService.record(
            entity_type="agent", entity_id="a1", type="agent.updated", data={"agent_id": "a1"}
        )
    )

    logs = client.get("/api/v1/logs", headers=OWNER_HEADERS).json()
    assert any(r["type"] == "agent.updated" for r in logs)  # event thật hiển thị
    assert all(r["category"] != "idempotency_batch" for r in logs)  # event nội bộ bị loại
