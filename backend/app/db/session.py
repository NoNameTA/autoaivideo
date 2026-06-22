"""Async engine + session factory (SPEC 04 §1, 10 §5/§6).

SQLite bật foreign_keys + WAL. Postgres dùng cùng API (SQLAlchemy portable).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()


def _ensure_sqlite_dir(database_url: str) -> None:
    """Tạo thư mục chứa file SQLite nếu chưa có (tránh 'unable to open database file')."""
    if database_url.startswith("sqlite") and ":///" in database_url:
        db_path = database_url.split(":///", 1)[1]
        if db_path and ":memory:" not in db_path:
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(_settings.database_url)

engine = create_async_engine(_settings.database_url, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


if _settings.database_url.startswith("sqlite"):

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _record) -> None:  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.execute("PRAGMA journal_mode=WAL")
        cur.close()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
