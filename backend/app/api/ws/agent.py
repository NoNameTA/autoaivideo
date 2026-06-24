"""WebSocket cho Desktop Agent `/ws/agent` (SPEC 09 §4).

Đăng ký kết nối vào AgentRegistry để dispatcher gửi step.assign; chuyển kết quả step về
OrchestratorEngine; persist agent + broadcast trạng thái.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.api.ws.fs_rpc import fs_rpc
from app.api.ws.manager import envelope, manager
from app.core.config import get_settings
from app.core.errors import AppError, ForbiddenError, UnauthorizedError, ValidationAppError
from app.core.security import verify_agent_token
from app.db.session import SessionLocal
from app.models.step import Step
from app.orchestrator.agent_registry import AgentConn, registry
from app.orchestrator.engine import engine
from app.services.agent_service import AgentService
from app.services.allowed_folder_service import AllowedFolderService
from app.services.connection_service import ConnectionService
from app.services.credential_service import CredentialService

router = APIRouter()


async def _handle_credential_request(
    websocket: WebSocket, agent_id: str | None, data: dict
) -> None:
    """Cấp credential JIT cho Agent (SPEC 09 §4.3, 11 §3.3). Chỉ token ngắn hạn tối thiểu."""
    req_id = data.get("request_id")
    try:
        async with SessionLocal() as session:
            step_id = data.get("step_id")
            step = await session.get(Step, step_id) if step_id else None
            # Đối soát: step phải đang được giao cho chính agent này.
            if agent_id is None or step is None or step.assigned_agent != agent_id:
                raise ForbiddenError("Step không thuộc agent này")
            cred_ref = data.get("credential_ref")
            conn_id = data.get("connection_id")
            if conn_id and not cred_ref:
                conn = await ConnectionService.get(session, conn_id)
                cred_ref = conn.credential_id
            if not cred_ref:
                raise ValidationAppError("Thiếu credential_ref/connection_id")
            cred = await CredentialService.get(session, cred_ref)
            token, expires_at = await CredentialService.mint_token(
                session, cred, data.get("scopes") or None
            )
        await websocket.send_json(
            envelope(
                "credential.response",
                {
                    "request_id": req_id,
                    "ok": True,
                    "material": {"type": "bearer", "token": token, "header": "Authorization"},
                    "expires_at": expires_at,
                },
            )
        )
    except AppError as e:
        await websocket.send_json(
            envelope(
                "credential.response",
                {
                    "request_id": req_id,
                    "ok": False,
                    "error": {"code": e.code, "message": e.message},
                },
            )
        )
    except Exception as e:  # noqa: BLE001 - không lộ chi tiết bí mật
        await websocket.send_json(
            envelope(
                "credential.response",
                {
                    "request_id": req_id,
                    "ok": False,
                    "error": {"code": "INTERNAL", "message": type(e).__name__},
                },
            )
        )


@router.websocket("/ws/agent")
async def ws_agent(websocket: WebSocket, token: str | None = Query(default=None)) -> None:
    try:
        verify_agent_token(token, get_settings())
    except UnauthorizedError:
        await websocket.close(code=4401)
        return

    await websocket.accept()
    agent_id: str | None = None
    try:
        while True:
            msg = await websocket.receive_json()
            mtype = msg.get("type")
            data = msg.get("data", {}) or {}

            if mtype == "agent.register":
                async with SessionLocal() as session:
                    agent = await AgentService.register(session, data)
                    allowed = await AllowedFolderService.paths(session)
                agent_id = agent.id
                registry.add(
                    AgentConn(
                        agent_id=agent.id,
                        ws=websocket,
                        capabilities=list(agent.capabilities),
                        capacity=agent.capacity,
                    )
                )
                # Đẩy Allowed Folders xuống agent (SPEC 11 §5).
                await registry.send(
                    agent.id, envelope("config.update", {"allowed_folders": allowed})
                )
                await manager.broadcast(
                    "agent.updated",
                    {"agent_id": agent.id, "status": agent.status, "capacity": agent.capacity},
                )
            elif mtype == "heartbeat":
                aid = data.get("agent_id", agent_id)
                if aid:
                    async with SessionLocal() as session:
                        await AgentService.heartbeat(session, aid)
            elif mtype == "step.ack":
                await engine.on_ack(data["step_id"])
            elif mtype == "step.progress":
                await engine.on_progress(data.get("step_id"), data.get("pct"))
            elif mtype == "step.completed":
                await engine.on_completed(data["step_id"], data.get("assets", []))
            elif mtype == "step.failed":
                await engine.on_failed(
                    data["step_id"],
                    data.get("error", "unknown"),
                    bool(data.get("retryable", False)),
                )
            elif mtype == "credential.request":
                await _handle_credential_request(websocket, agent_id, data)
            elif mtype == "fs.response":
                fs_rpc.resolve(
                    data.get("request_id"),
                    bool(data.get("ok")),
                    data.get("result"),
                    data.get("error"),
                )
            elif mtype == "fs.event":
                await manager.broadcast("fs.event", data)
    except WebSocketDisconnect:
        if agent_id:
            registry.remove(agent_id)
            async with SessionLocal() as session:
                await AgentService.set_offline(session, agent_id)
            await manager.broadcast(
                "agent.updated", {"agent_id": agent_id, "status": "offline", "capacity": 0}
            )
