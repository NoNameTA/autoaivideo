"""Dependencies dùng chung cho API (SPEC 04 §1, 11)."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from app.core.security import extract_bearer, verify_owner_token
from app.db.session import get_session


async def require_owner(
    authorization: Annotated[str | None, Header()] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,  # type: ignore[assignment]
) -> None:
    verify_owner_token(extract_bearer(authorization), settings)


def page_params(
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
    cursor: Annotated[str | None, Query()] = None,
) -> tuple[int, str | None]:
    return limit, cursor


SessionDep = Annotated[AsyncSession, Depends(get_session)]
PageDep = Annotated[tuple[int, str | None], Depends(page_params)]
