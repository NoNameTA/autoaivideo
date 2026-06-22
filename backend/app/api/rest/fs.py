"""REST File Manager (SPEC 07). Mọi thao tác validate Allowed Folders rồi forward tới agent."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.fs import (
    AllowedFolderCreate,
    AllowedFolderOut,
    CopyMoveBody,
    PathBody,
    ReadBody,
    RenameBody,
    WatchBody,
)
from app.services.allowed_folder_service import AllowedFolderService
from app.services.fs_service import FsService

router = APIRouter(prefix="/api/v1/fs", tags=["fs"], dependencies=[Depends(require_owner)])


# ----- Allowed Folders (Permission Manager) -----
@router.get("/allowed", response_model=list[AllowedFolderOut])
async def list_allowed(session: SessionDep) -> list[AllowedFolderOut]:
    return await AllowedFolderService.list(session)  # type: ignore[return-value]


@router.post("/allowed", response_model=AllowedFolderOut, status_code=status.HTTP_201_CREATED)
async def add_allowed(data: AllowedFolderCreate, session: SessionDep) -> AllowedFolderOut:
    folder = await AllowedFolderService.add(session, data)
    await FsService.push_allowed(session)
    return folder  # type: ignore[return-value]


@router.delete("/allowed/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_allowed(folder_id: str, session: SessionDep):
    await AllowedFolderService.remove(session, folder_id)
    await FsService.push_allowed(session)


# ----- Thao tác file (forward tới agent) -----
@router.post("/scan")
async def scan(body: PathBody, session: SessionDep) -> dict:
    return await FsService.call(session, "scan", {"path": body.path}, [body.path])


@router.post("/read")
async def read(body: ReadBody, session: SessionDep) -> dict:
    return await FsService.call(
        session, "read", {"path": body.path, "max_bytes": body.max_bytes}, [body.path]
    )


@router.post("/metadata")
async def metadata(body: PathBody, session: SessionDep) -> dict:
    return await FsService.call(session, "metadata", {"path": body.path}, [body.path])


@router.post("/copy")
async def copy(body: CopyMoveBody, session: SessionDep) -> dict:
    return await FsService.call(
        session, "copy", {"src": body.src, "dst": body.dst}, [body.src, body.dst]
    )


@router.post("/move")
async def move(body: CopyMoveBody, session: SessionDep) -> dict:
    return await FsService.call(
        session, "move", {"src": body.src, "dst": body.dst}, [body.src, body.dst]
    )


@router.post("/rename")
async def rename(body: RenameBody, session: SessionDep) -> dict:
    return await FsService.call(
        session, "rename", {"path": body.path, "new_name": body.new_name}, [body.path]
    )


@router.post("/delete")
async def delete(body: PathBody, session: SessionDep) -> dict:
    return await FsService.call(session, "delete", {"path": body.path}, [body.path])


@router.post("/watch")
async def watch(body: WatchBody, session: SessionDep) -> dict:
    return await FsService.call(
        session, "watch", {"path": body.path, "enable": body.enable}, [body.path]
    )
