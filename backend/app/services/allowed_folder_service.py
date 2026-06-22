from __future__ import annotations

import os

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.allowed_folder import AllowedFolder
from app.schemas.fs import AllowedFolderCreate


def is_within_allowed(path: str, allowed: list[str]) -> bool:
    """True nếu path nằm trong một thư mục được phép (chống traversal, SPEC 11 §5)."""
    try:
        rp = os.path.realpath(path)
    except OSError:
        return False
    for root in allowed:
        rr = os.path.realpath(root)
        if rp == rr or rp.startswith(rr + os.sep):
            return True
    return False


class AllowedFolderService:
    @staticmethod
    async def list(session: AsyncSession) -> list[AllowedFolder]:
        return list((await session.execute(select(AllowedFolder))).scalars().all())

    @staticmethod
    async def paths(session: AsyncSession) -> list[str]:
        return [f.path for f in await AllowedFolderService.list(session)]

    @staticmethod
    async def add(session: AsyncSession, data: AllowedFolderCreate) -> AllowedFolder:
        norm = os.path.normpath(data.path)
        existing = (
            await session.execute(select(AllowedFolder).where(AllowedFolder.path == norm))
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        folder = AllowedFolder(path=norm, label=data.label or os.path.basename(norm) or norm)
        session.add(folder)
        await session.commit()
        await session.refresh(folder)
        return folder

    @staticmethod
    async def remove(session: AsyncSession, folder_id: str) -> None:
        folder = await session.get(AllowedFolder, folder_id)
        if folder is None:
            raise NotFoundError(f"Allowed folder '{folder_id}' không tồn tại")
        await session.delete(folder)
        await session.commit()
