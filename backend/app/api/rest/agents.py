from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_owner
from app.schemas.agent import AgentOut
from app.services.agent_service import AgentService

router = APIRouter(prefix="/api/v1/agents", tags=["agents"], dependencies=[Depends(require_owner)])


@router.get("", response_model=list[AgentOut])
async def list_agents(session: SessionDep) -> list[AgentOut]:
    return await AgentService.list(session)  # type: ignore[return-value]
