from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utcnow
from app.models.agent import Agent
from app.models.enums import AgentStatus


class AgentService:
    @staticmethod
    async def list(session: AsyncSession) -> list[Agent]:
        return list((await session.execute(select(Agent))).scalars().all())

    @staticmethod
    async def register(session: AsyncSession, payload: dict) -> Agent:
        agent_id = payload["agent_id"]
        agent = await session.get(Agent, agent_id)
        if agent is None:
            agent = Agent(id=agent_id)
            session.add(agent)
        agent.version = payload.get("version", agent.version or "")
        agent.capabilities = payload.get("capabilities", [])
        agent.capacity = int(payload.get("capacity", 1))
        agent.os = payload.get("os", agent.os or "")
        agent.status = AgentStatus.online
        agent.last_heartbeat = utcnow()
        await session.commit()
        await session.refresh(agent)
        return agent

    @staticmethod
    async def heartbeat(session: AsyncSession, agent_id: str) -> None:
        agent = await session.get(Agent, agent_id)
        if agent is None:
            return
        agent.last_heartbeat = utcnow()
        if agent.status == AgentStatus.offline:
            agent.status = AgentStatus.online
        await session.commit()

    @staticmethod
    async def set_offline(session: AsyncSession, agent_id: str) -> None:
        agent = await session.get(Agent, agent_id)
        if agent is None:
            return
        agent.status = AgentStatus.offline
        await session.commit()
