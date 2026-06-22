"""Điều phối thao tác File Manager: validate Allowed Folders (SPEC 11 §5) + forward tới agent."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ws.fs_rpc import fs_rpc
from app.api.ws.manager import envelope
from app.core.errors import AgentUnavailableError, ForbiddenError
from app.orchestrator.agent_registry import registry
from app.services.allowed_folder_service import AllowedFolderService, is_within_allowed


class FsService:
    @staticmethod
    def _pick_agent() -> str:
        agent_id = registry.first_agent_id()
        if agent_id is None:
            raise AgentUnavailableError("Không có Desktop Agent online")
        return agent_id

    @staticmethod
    async def _ensure_allowed(session: AsyncSession, *paths: str) -> None:
        allowed = await AllowedFolderService.paths(session)
        for p in paths:
            if not is_within_allowed(p, allowed):
                raise ForbiddenError(f"Đường dẫn ngoài Allowed Folders: {p}")

    @staticmethod
    async def call(
        session: AsyncSession, op: str, params: dict, check_paths: list[str]
    ) -> dict:
        await FsService._ensure_allowed(session, *check_paths)
        agent_id = FsService._pick_agent()
        return await fs_rpc.call(agent_id, op, params)

    @staticmethod
    async def push_allowed(session: AsyncSession) -> None:
        paths = await AllowedFolderService.paths(session)
        await registry.send_all(envelope("config.update", {"allowed_folders": paths}))
