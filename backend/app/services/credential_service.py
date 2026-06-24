"""Credential Store service (SPEC 11 §3.1). Backend là nơi DUY NHẤT giữ & giải mã secret.

API chỉ phơi metadata; material chỉ giải mã nội bộ để mint token ngắn hạn (SPEC 11 §3.3).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cloud.google_auth import mint_service_account_token
from app.core.errors import NotFoundError, ValidationAppError
from app.db.base import utcnow
from app.models.credential import Credential
from app.schemas.credential import CredentialCreate
from app.secrets.provider import SecretError, get_secret_provider, provider_by_backend


class CredentialService:
    @staticmethod
    async def list(session: AsyncSession) -> list[Credential]:
        stmt = select(Credential).order_by(Credential.created_at.desc())
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def get(session: AsyncSession, cred_id: str) -> Credential:
        cred = await session.get(Credential, cred_id)
        if cred is None:
            raise NotFoundError(f"Credential '{cred_id}' không tồn tại")
        return cred

    @staticmethod
    async def create(session: AsyncSession, data: CredentialCreate) -> Credential:
        provider = get_secret_provider()  # db_store nếu có MASTER_KEY, ngược lại local_file
        if provider.name == "db_store":
            material = data.secret_inline
            if not material:
                raise ValidationAppError("db_store cần `secret_inline` (material thô)")
        else:  # local_file
            material = data.secret_path
            if not material:
                raise ValidationAppError("local_file cần `secret_path` (đường dẫn file bí mật)")

        try:
            stored = provider.put(material)
        except SecretError as e:
            raise ValidationAppError(str(e)) from None

        cred = Credential(
            provider=data.provider,
            connection_name=data.connection_name,
            authentication_type=data.authentication_type,
            encrypted_secret=stored,
            cred_metadata={"backend": provider.name, "scopes": data.scopes},
            status="active",
        )
        session.add(cred)
        await session.commit()
        await session.refresh(cred)
        return cred

    @staticmethod
    async def delete(session: AsyncSession, cred_id: str) -> None:
        cred = await CredentialService.get(session, cred_id)
        await session.delete(cred)
        await session.commit()

    # ----- nội bộ (KHÔNG phơi qua API) -----
    @staticmethod
    def resolve_material(cred: Credential) -> str:
        """Giải mã/đọc material gốc (vd Service Account JSON). Chỉ dùng nội bộ Backend."""
        backend = (cred.cred_metadata or {}).get("backend", "local_file")
        return provider_by_backend(backend).get(cred.encrypted_secret)

    @staticmethod
    async def mint_token(
        session: AsyncSession, cred: Credential, scopes: list[str] | None = None
    ) -> tuple[str, int]:
        """Mint access token NGẮN HẠN tối thiểu cho operation (SPEC 11 §3.2–3.3)."""
        use_scopes = scopes or (cred.cred_metadata or {}).get("scopes") or []
        if cred.authentication_type != "service_account":
            raise ValidationAppError(
                f"V2.0 chỉ hỗ trợ service_account (gặp '{cred.authentication_type}')"
            )
        material = CredentialService.resolve_material(cred)
        token, expires_at = await mint_service_account_token(material, use_scopes)
        cred.last_used_at = utcnow()
        await session.commit()
        return token, expires_at
