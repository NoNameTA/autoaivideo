from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, require_owner
from app.schemas.external_app import ExternalAppOut, ExternalAppTestResult
from app.services.external_app_service import ExternalAppService

router = APIRouter(
    prefix="/api/v1/external-apps", tags=["external-apps"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[ExternalAppOut])
async def list_external_apps(session: SessionDep) -> list[ExternalAppOut]:
    return await ExternalAppService.list(session)  # type: ignore[return-value]


@router.post("/{name}/test", response_model=ExternalAppTestResult)
async def test_external_app(name: str, session: SessionDep) -> ExternalAppTestResult:
    return await ExternalAppService.test(session, name)  # type: ignore[return-value]
