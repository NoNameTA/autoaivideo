from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessionDep, require_owner
from app.core.constants import DEFAULT_PAGE_LIMIT, MAX_PAGE_LIMIT
from app.schemas.log import LogOut
from app.services.event_service import EventService

router = APIRouter(prefix="/api/v1/logs", tags=["logs"], dependencies=[Depends(require_owner)])


@router.get("", response_model=list[LogOut])
async def list_logs(
    session: SessionDep,
    level: Annotated[str | None, Query(pattern="^(info|warn|error|debug)$")] = None,
    category: Annotated[str | None, Query(max_length=40)] = None,
    project_id: Annotated[str | None, Query(max_length=40)] = None,
    batch_id: Annotated[str | None, Query(max_length=40)] = None,
    plugin: Annotated[str | None, Query(max_length=60)] = None,
    trace_id: Annotated[str | None, Query(max_length=40)] = None,
    search: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
) -> list[LogOut]:
    return await EventService.list(  # type: ignore[return-value]
        session,
        limit=limit,
        level=level,
        category=category,
        project_id=project_id,
        batch_id=batch_id,
        plugin=plugin,
        trace_id=trace_id,
        search=search,
    )
