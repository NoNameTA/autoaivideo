"""Test Video Sources (Pha 1, Direct URL). Tái dùng Batch/Queue thật, không mock."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.errors import ValidationAppError
from app.services.video_source_service import _parse_sheet
from tests.conftest import OWNER_HEADERS


def test_parse_sheet_extracts_url_column() -> None:
    values = [
        ["Title", "VideoURL", "Note"],
        ["Phim A", "https://example.com/a.mp4", "x"],
        ["Phim B", "xem ở https://example.com/b.mp4 nhé", "y"],
        ["", "https://example.com/a.mp4", "trùng"],  # dedup
        ["Phim C", "không có link", "z"],  # bỏ
    ]
    rows = _parse_sheet(values, "VideoURL", "Title")
    assert [u for u, _ in rows] == ["https://example.com/a.mp4", "https://example.com/b.mp4"]
    assert rows[0][1] == "Phim A"
    # Sai tên cột -> lỗi rõ ràng.
    with pytest.raises(ValidationAppError):
        _parse_sheet(values, "KhongCo", None)


def _create(client: TestClient, name: str = "Src A") -> str:
    r = client.post(
        "/api/v1/video-sources",
        json={"name": name, "source_type": "direct_url"},
        headers=OWNER_HEADERS,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_create_and_import_links(client: TestClient) -> None:
    sid = _create(client)
    # urls[] + text thô (paste nhiều dòng + 1 dòng kiểu CSV "title, url") + 1 trùng.
    r = client.post(
        f"/api/v1/video-sources/{sid}/links",
        json={
            "urls": ["https://example.com/a.mp4"],
            "text": (
                "Video B, https://example.com/b.mp4\n"
                "https://example.com/a.mp4\n"
                "# dòng không có link"
            ),
        },
        headers=OWNER_HEADERS,
    )
    assert r.status_code == 200, r.text
    assert r.json()["item_count"] == 2  # a (dedup) + b
    assert r.json()["status"] == "imported"

    items = client.get(f"/api/v1/video-sources/{sid}/items", headers=OWNER_HEADERS).json()
    assert len(items) == 2
    urls = {it["url"] for it in items}
    assert urls == {"https://example.com/a.mp4", "https://example.com/b.mp4"}
    titleb = next(it for it in items if it["url"].endswith("b.mp4"))["title"]
    assert titleb == "Video B"
    assert all(it["status"] == "pending" for it in items)


def test_import_rejects_no_url(client: TestClient) -> None:
    sid = _create(client)
    r = client.post(
        f"/api/v1/video-sources/{sid}/links",
        json={"text": "không có link nào ở đây"},
        headers=OWNER_HEADERS,
    )
    assert r.status_code == 422


def test_run_creates_one_job_per_link(client: TestClient) -> None:
    sid = _create(client, "Run src")
    client.post(
        f"/api/v1/video-sources/{sid}/links",
        json={"urls": ["https://example.com/x.mp4", "https://example.com/y.mp4"]},
        headers=OWNER_HEADERS,
    )
    r = client.post(f"/api/v1/video-sources/{sid}/run", json={}, headers=OWNER_HEADERS)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["job_count"] == 2
    batch_id = body["batch_id"]

    # Mỗi link -> 1 Job trong Queue (tái dùng Queue hiện có).
    jobs = client.get(f"/api/v1/jobs?search={batch_id}", headers=OWNER_HEADERS).json()
    assert len(jobs) == 2
    assert all(j["pipeline"] == "video_download" for j in jobs)
    # Job vars chứa url (Agent yt-dlp đọc 'url' từ inputs).
    assert all("url" in j["vars"] for j in jobs)

    # Item đã link job + status processing (suy từ job queued).
    items = client.get(f"/api/v1/video-sources/{sid}/items", headers=OWNER_HEADERS).json()
    assert all(it["job_id"] for it in items)
    assert all(it["status"] == "processing" for it in items)

    # Source -> running.
    src = client.get(f"/api/v1/video-sources/{sid}", headers=OWNER_HEADERS).json()
    assert src["status"] == "running"


def test_google_sheets_source_requires_connection(client: TestClient) -> None:
    # Nguồn google_sheets thiếu connection_id -> read/import báo lỗi rõ (không mock).
    r = client.post(
        "/api/v1/video-sources",
        json={"name": "GS", "source_type": "google_sheets", "config": {"url_column": "VideoURL"}},
        headers=OWNER_HEADERS,
    )
    assert r.status_code == 201
    sid = r.json()["id"]
    rr = client.post(f"/api/v1/video-sources/{sid}/read-sheet", headers=OWNER_HEADERS)
    assert rr.status_code == 422
    ri = client.post(f"/api/v1/video-sources/{sid}/import-sheet", headers=OWNER_HEADERS)
    assert ri.status_code == 422


def test_delete_source(client: TestClient) -> None:
    sid = _create(client)
    client.post(
        f"/api/v1/video-sources/{sid}/links",
        json={"urls": ["https://example.com/z.mp4"]},
        headers=OWNER_HEADERS,
    )
    assert client.delete(f"/api/v1/video-sources/{sid}", headers=OWNER_HEADERS).status_code == 204
    assert client.get(f"/api/v1/video-sources/{sid}", headers=OWNER_HEADERS).status_code == 404
