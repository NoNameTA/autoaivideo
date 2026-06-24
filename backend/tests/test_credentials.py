"""Test Credential Store + Secret Provider + Connection (SPEC 11 §3, 06 §10).

Dùng mã hoá Fernet THẬT + file IO thật (không mock). Phần gọi Google cần credential thật → để
integration test riêng (không giả lập dữ liệu).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.secrets.provider import (
    DbStoreProvider,
    LocalFileProvider,
    SecretError,
)
from tests.conftest import OWNER_HEADERS


def test_db_store_provider_roundtrip() -> None:
    key = Fernet.generate_key().decode()
    p = DbStoreProvider(key)
    stored = p.put('{"hello":"world"}')
    assert stored != '{"hello":"world"}'  # đã mã hoá
    assert p.get(stored) == '{"hello":"world"}'
    # MASTER_KEY khác -> không giải mã được.
    with pytest.raises(SecretError):
        DbStoreProvider(Fernet.generate_key().decode()).get(stored)


def test_local_file_provider(tmp_path: Path) -> None:
    secret = tmp_path / "sa.json"
    secret.write_text('{"type":"service_account"}', encoding="utf-8")
    p = LocalFileProvider(str(tmp_path))
    stored = p.put("sa.json")
    assert stored == "sa.json"
    assert p.get("sa.json") == '{"type":"service_account"}'
    # Chống path traversal.
    with pytest.raises(SecretError):
        p.get("../outside.json")
    # File không tồn tại.
    with pytest.raises(SecretError):
        p.put("khongco.json")


def _make_secret_file(name: str) -> Path:
    base = Path(get_settings().secrets_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)
    f = base / name
    f.write_text('{"type":"service_account","client_email":"x"}', encoding="utf-8")
    return f


def test_credentials_api_no_secret_leak(client: TestClient) -> None:
    f = _make_secret_file("uat_test_sa.json")
    try:
        r = client.post(
            "/api/v1/credentials",
            json={
                "provider": "google_sheets",
                "connection_name": "UAT cred",
                "authentication_type": "service_account",
                "scopes": ["https://www.googleapis.com/auth/spreadsheets"],
                "secret_path": "uat_test_sa.json",
            },
            headers=OWNER_HEADERS,
        )
        assert r.status_code == 201, r.text
        body = r.json()
        # KHÔNG bao giờ lộ bí mật.
        assert "encrypted_secret" not in body
        assert "private_key" not in r.text
        assert body["provider"] == "google_sheets"
        assert body["metadata"]["backend"] == "local_file"

        listed = client.get("/api/v1/credentials", headers=OWNER_HEADERS).json()
        assert any(c["id"] == body["id"] for c in listed)
        assert all("encrypted_secret" not in c for c in listed)

        # Xoá.
        d = client.delete(f"/api/v1/credentials/{body['id']}", headers=OWNER_HEADERS)
        assert d.status_code == 204
    finally:
        f.unlink(missing_ok=True)


def test_connections_api_crud_and_test(client: TestClient) -> None:
    r = client.post(
        "/api/v1/connections",
        json={
            "provider": "google_sheets",
            "display_name": "Sheet UAT",
            "capabilities": ["cloud.google_sheets.read"],
            "settings": {"spreadsheet_id": "abc", "worksheet": "Sheet1"},
        },
        headers=OWNER_HEADERS,
    )
    assert r.status_code == 201, r.text
    conn = r.json()
    assert conn["health_status"] == "unknown"
    assert conn["settings"]["spreadsheet_id"] == "abc"

    # Test kết nối khi chưa gắn credential -> ok=false (endpoint hoạt động, không mock).
    t = client.post(f"/api/v1/connections/{conn['id']}/test", headers=OWNER_HEADERS).json()
    assert t["ok"] is False
    assert t["health_status"] == "error"

    d = client.delete(f"/api/v1/connections/{conn['id']}", headers=OWNER_HEADERS)
    assert d.status_code == 204
