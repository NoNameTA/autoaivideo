from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_owner
from app.schemas.stats import StatsOut
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api/v1/stats", tags=["stats"], dependencies=[Depends(require_owner)])


@router.get("", response_model=StatsOut)
async def get_stats(session: SessionDep) -> StatsOut:
    return await StatsService.compute(session)  # type: ignore[return-value]
