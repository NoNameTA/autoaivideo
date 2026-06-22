from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.pagination import paginate


class ProjectService:
    @staticmethod
    async def create(session: AsyncSession, data: ProjectCreate) -> Project:
        project = Project(**data.model_dump())
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    @staticmethod
    async def get(session: AsyncSession, project_id: str) -> Project:
        project = await session.get(Project, project_id)
        if not project:
            raise NotFoundError(f"Project '{project_id}' không tồn tại")
        return project

    @staticmethod
    async def list(
        session: AsyncSession, limit: int, cursor: str | None
    ) -> tuple[list[Project], str | None]:
        return await paginate(session, select(Project), Project.id, limit, cursor)

    @staticmethod
    async def update(session: AsyncSession, project_id: str, data: ProjectUpdate) -> Project:
        project = await ProjectService.get(session, project_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(project, key, value)
        await session.commit()
        await session.refresh(project)
        return project

    @staticmethod
    async def delete(session: AsyncSession, project_id: str) -> None:
        project = await ProjectService.get(session, project_id)
        await session.delete(project)
        await session.commit()
