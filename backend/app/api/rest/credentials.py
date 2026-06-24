from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.credential import CredentialCreate, CredentialOut
from app.services.credential_service import CredentialService

router = APIRouter(
    prefix="/api/v1/credentials", tags=["credentials"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[CredentialOut])
async def list_credentials(session: SessionDep) -> list[CredentialOut]:
    return await CredentialService.list(session)  # type: ignore[return-value]


@router.post("", response_model=CredentialOut, status_code=status.HTTP_201_CREATED)
async def create_credential(data: CredentialCreate, session: SessionDep) -> CredentialOut:
    return await CredentialService.create(session, data)  # type: ignore[return-value]


@router.delete("/{cred_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(cred_id: str, session: SessionDep):
    await CredentialService.delete(session, cred_id)
