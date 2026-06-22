from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import PageDep, SessionDep, require_owner
from app.schemas.common import Page
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(
    prefix="/api/v1/projects", tags=["projects"], dependencies=[Depends(require_owner)]
)


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, session: SessionDep) -> ProjectOut:
    return await ProjectService.create(session, data)  # type: ignore[return-value]


@router.get("", response_model=Page[ProjectOut])
async def list_projects(session: SessionDep, page: PageDep) -> Page[ProjectOut]:
    limit, cursor = page
    items, next_cursor = await ProjectService.list(session, limit, cursor)
    return Page[ProjectOut](items=items, next_cursor=next_cursor)  # type: ignore[arg-type]


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, session: SessionDep) -> ProjectOut:
    return await ProjectService.get(session, project_id)  # type: ignore[return-value]


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: str, data: ProjectUpdate, session: SessionDep
) -> ProjectOut:
    return await ProjectService.update(session, project_id, data)  # type: ignore[return-value]


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, session: SessionDep):
    await ProjectService.delete(session, project_id)
