"""Phân trang con trỏ theo khoá chính (SPEC 09 §5). ID là ULID nên so sánh được."""

from __future__ import annotations

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession


async def paginate(
    session: AsyncSession,
    stmt: Select,
    id_column,  # noqa: ANN001 - cột khoá chính của model
    limit: int,
    cursor: str | None,
) -> tuple[list, str | None]:
    stmt = stmt.order_by(id_column).limit(limit + 1)
    if cursor:
        stmt = stmt.where(id_column > cursor)
    rows = list((await session.execute(stmt)).scalars().all())
    next_cursor = None
    if len(rows) > limit:
        rows = rows[:limit]
        next_cursor = getattr(rows[-1], id_column.key)
    return rows, next_cursor
