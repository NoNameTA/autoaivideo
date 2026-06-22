"""Fixtures test — DB SQLite tạm, tách biệt, tạo schema thật từ metadata (SPEC 15 §2)."""

from __future__ import annotations

import asyncio
import os
import tempfile
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401 - nạp model vào metadata
from app.db.base import Base
from app.db.session import get_session
from app.main import app

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
_TEST_URL = f"sqlite+aiosqlite:///{_tmp.name}"

_engine = create_async_engine(_TEST_URL)
_Session = async_sessionmaker(_engine, expire_on_commit=False)

OWNER_HEADERS = {"Authorization": "Bearer change-me-owner-token"}


async def _override_session() -> AsyncIterator:
    async with _Session() as session:
        yield session


app.dependency_overrides[get_session] = _override_session

# Engine dùng SessionLocal trực tiếp -> trỏ về DB test để cô lập.
import app.orchestrator.engine as _engine_module  # noqa: E402

_engine_module.SessionLocal = _Session


# Tắt vòng lặp nền của engine trong test (tránh ghi DB song song với reset schema).
# Vẫn test trực tiếp các handler on_*/advance.
async def _noop() -> None:
    return None


_engine_module.engine.start = _noop  # type: ignore[method-assign]
_engine_module.engine.stop = _noop  # type: ignore[method-assign]


async def _reset_schema() -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(autouse=True)
def reset_db() -> Iterator[None]:
    asyncio.run(_reset_schema())
    yield


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def pytest_sessionfinish(session, exitstatus) -> None:  # noqa: ANN001, ARG001
    try:
        os.unlink(_tmp.name)
    except OSError:
        pass
