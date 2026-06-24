"""Connection Manager service (SPEC 06 §10, 11 §3.4). Connection KHÔNG chứa bí mật.

Test kết nối = healthcheck THẬT (mint token + gọi API provider). Không mock.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cloud import google_sheets
from app.core.errors import NotFoundError, ValidationAppError
from app.db.base import utcnow
from app.models.connection import Connection
from app.schemas.connection import ConnectionCreate, ConnectionUpdate
from app.secrets.provider import SecretError
from app.services.credential_service import CredentialService

# Provider -> nhóm capability (Provider Framework, SPEC 06 §9.8).
_GOOGLE_SHEETS = "google_sheets"


class ConnectionService:
    @staticmethod
    async def list(session: AsyncSession) -> list[Connection]:
        stmt = select(Connection).order_by(Connection.created_at.desc())
        return list((await session.execute(stmt)).scalars().all())

    @staticmethod
    async def get(session: AsyncSession, conn_id: str) -> Connection:
        conn = await session.get(Connection, conn_id)
        if conn is None:
            raise NotFoundError(f"Connection '{conn_id}' không tồn tại")
        return conn

    @staticmethod
    async def create(session: AsyncSession, data: ConnectionCreate) -> Connection:
        conn = Connection(
            provider=data.provider,
            credential_id=data.credential_id,
            display_name=data.display_name,
            capabilities=data.capabilities,
            settings=data.settings,
            health_status="unknown",
        )
        session.add(conn)
        await session.commit()
        await session.refresh(conn)
        return conn

    @staticmethod
    async def update(session: AsyncSession, conn_id: str, data: ConnectionUpdate) -> Connection:
        conn = await ConnectionService.get(session, conn_id)
        for field in ("credential_id", "display_name", "enabled", "capabilities", "settings"):
            val = getattr(data, field)
            if val is not None:
                setattr(conn, field, val)
        await session.commit()
        await session.refresh(conn)
        return conn

    @staticmethod
    async def delete(session: AsyncSession, conn_id: str) -> None:
        conn = await ConnectionService.get(session, conn_id)
        await session.delete(conn)
        await session.commit()

    @staticmethod
    async def test(session: AsyncSession, conn_id: str) -> dict:
        """Test kết nối THẬT: mint token + gọi API provider. Cập nhật health_status/last_check."""
        conn = await ConnectionService.get(session, conn_id)
        result = await ConnectionService._run_healthcheck(session, conn)
        conn.health_status = "connected" if result["ok"] else "error"
        conn.last_check = utcnow()
        await session.commit()
        # Log nghiệp vụ (SPEC Logs v1.0 §9): GoogleSheets.Connect — KHÔNG log token/secret.
        from app.services.event_service import EventService

        await EventService.record(
            entity_type="connection",
            entity_id=conn.id,
            type="GoogleSheets.Connect",
            data={
                "ok": result["ok"],
                "provider": conn.provider,
                **({"title": result["title"]} if result.get("title") else {}),
                **({"error": result["error"]} if not result["ok"] and result.get("error") else {}),
            },
            level=None if result["ok"] else "error",
        )
        return {
            "ok": result["ok"],
            "health_status": conn.health_status,
            "message": result.get("title")
            and f"Kết nối OK: {result['title']}"
            or result.get("error", "Không xác định"),
        }

    @staticmethod
    async def _run_healthcheck(session: AsyncSession, conn: Connection) -> dict:
        if not conn.credential_id:
            return {"ok": False, "error": "Connection chưa gắn credential"}
        if conn.provider != _GOOGLE_SHEETS:
            return {"ok": False, "error": f"Provider '{conn.provider}' chưa hỗ trợ test (V2.0)"}
        try:
            cred = await CredentialService.get(session, conn.credential_id)
            token, _ = await CredentialService.mint_token(session, cred)
        except (SecretError, ValidationAppError) as e:
            return {"ok": False, "error": str(e)}
        spreadsheet_id = (conn.settings or {}).get("spreadsheet_id", "")
        return await google_sheets.healthcheck(token, spreadsheet_id)
