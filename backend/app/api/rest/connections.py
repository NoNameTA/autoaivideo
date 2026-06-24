from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.connection import (
    ConnectionCreate,
    ConnectionOut,
    ConnectionTestResult,
    ConnectionUpdate,
)
from app.services.connection_service import ConnectionService

router = APIRouter(
    prefix="/api/v1/connections", tags=["connections"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[ConnectionOut])
async def list_connections(session: SessionDep) -> list[ConnectionOut]:
    return await ConnectionService.list(session)  # type: ignore[return-value]


@router.post("", response_model=ConnectionOut, status_code=status.HTTP_201_CREATED)
async def create_connection(data: ConnectionCreate, session: SessionDep) -> ConnectionOut:
    return await ConnectionService.create(session, data)  # type: ignore[return-value]


@router.patch("/{conn_id}", response_model=ConnectionOut)
async def update_connection(
    conn_id: str, data: ConnectionUpdate, session: SessionDep
) -> ConnectionOut:
    return await ConnectionService.update(session, conn_id, data)  # type: ignore[return-value]


@router.delete("/{conn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(conn_id: str, session: SessionDep):
    await ConnectionService.delete(session, conn_id)


@router.post("/{conn_id}/test", response_model=ConnectionTestResult)
async def test_connection(conn_id: str, session: SessionDep) -> ConnectionTestResult:
    return await ConnectionService.test(session, conn_id)  # type: ignore[return-value]
