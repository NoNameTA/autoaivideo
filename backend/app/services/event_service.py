"""Audit-log có cấu trúc trên bảng `events` (SPEC 04 §7, 10 §2).

Mọi activity (engine + plugin lifecycle) đi qua đây để vừa **ghi vào DB** (cho trang
Logs đọc lịch sử) vừa **broadcast realtime** kênh `activity` (Dashboard + Logs live).
`level` được **suy ra từ loại event** lúc ghi — không yêu cầu caller truyền.
"""
from __future__ import annotations

from typing import Any, cast

from sqlalchemy import String, or_, select
from sqlalchemy import cast as sa_cast
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ws.manager import manager
from app.db.session import SessionLocal
from app.models.batch import Batch
from app.models.event import Event
from app.models.job import Job

# Loại entity nội bộ (idempotency key tạo batch) — không hiển thị ở trang Logs.
INTERNAL_ENTITY = "idempotency_batch"

# Job/step status mang ý nghĩa cảnh báo/lỗi (SPEC 12 §4).
_ERROR_STATUS = {"failed"}
_WARN_STATUS = {"cancelled", "retrying"}


def level_for(kind: str, data: dict[str, Any] | None = None) -> str:
    """Suy mức độ log từ loại event (SPEC 04 §7). Thuần, không side-effect."""
    data = data or {}
    k = kind.lower()
    status = str(data.get("status", "")).lower()
    if k.endswith(".failed") or k.endswith("registration_failed") or status in _ERROR_STATUS:
        return "error"
    if (
        k.endswith(".retrying")
        or "retry" in k
        or "timeout" in k
        or k.endswith(".disabled")
        or k.endswith(".removed")
        or status in _WARN_STATUS
    ):
        return "warn"
    if k.endswith(".progress"):
        return "debug"
    return "info"


def _infer_entity(kind: str, data: dict[str, Any]) -> tuple[str, str]:
    """Suy (entity_type, entity_id) từ loại event để lọc theo nhóm ở trang Logs."""
    if kind.startswith("plugin."):
        return "plugin", str(data.get("capability") or data.get("name") or "")
    # Log nghiệp vụ v1.0: Video.Download.* / Workflow.* gắn vào job để lọc theo job.
    if (kind.startswith(("Video.Download", "Workflow"))) and data.get("job_id"):
        return "job", str(data.get("job_id"))
    if kind.startswith("job"):
        return "job", str(data.get("job_id") or "")
    if kind.startswith("step"):
        return "step", str(data.get("step_id") or "")
    if kind.startswith("agent"):
        return "agent", str(data.get("agent_id") or "")
    if kind.startswith("fs"):
        return "fs", str(data.get("path") or "")
    return "system", ""


class EventService:
    @staticmethod
    async def from_activity(kind: str, data: dict[str, Any]) -> None:
        """Điểm vào cho các activity của engine/plugin: suy entity + level, ghi + phát."""
        entity_type, entity_id = _infer_entity(kind, data)
        await EventService.record(
            entity_type=entity_type,
            entity_id=entity_id,
            type=kind,
            data=data,
            broadcast=True,
        )

    @staticmethod
    async def record(
        *,
        entity_type: str,
        entity_id: str,
        type: str,
        data: dict[str, Any] | None = None,
        trace_id: str | None = None,
        level: str | None = None,
        broadcast: bool = True,
    ) -> None:
        """Ghi 1 event (transaction riêng, an toàn gọi sau khi caller đã commit)."""
        payload = dict(data or {})
        lvl = level or level_for(type, payload)
        async with SessionLocal() as session:
            await EventService._enrich(session, payload)
            session.add(
                Event(
                    trace_id=trace_id,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    type=type,
                    level=lvl,
                    data=payload,
                )
            )
            await session.commit()
        if broadcast:
            await manager.broadcast("activity", {"kind": type, "level": lvl, **payload})

    @staticmethod
    async def _enrich(session: AsyncSession, data: dict[str, Any]) -> None:
        """Bổ sung batch_id/project_id (denormalize) để Logs lọc theo batch/project."""
        if data.get("job_id") and not data.get("batch_id"):
            job = await session.get(Job, str(data["job_id"]))
            if job is not None:
                data["batch_id"] = job.batch_id
        if data.get("batch_id") and not data.get("project_id"):
            batch = await session.get(Batch, str(data["batch_id"]))
            if batch is not None:
                data["project_id"] = batch.project_id

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        limit: int,
        level: str | None = None,
        category: str | None = None,
        project_id: str | None = None,
        batch_id: str | None = None,
        plugin: str | None = None,
        trace_id: str | None = None,
        search: str | None = None,
    ) -> list[Event]:
        """Danh sách log cho trang Logs (mới nhất trước; lọc nhiều chiều)."""
        stmt = (
            select(Event)
            .where(Event.entity_type != INTERNAL_ENTITY)
            .order_by(Event.created_at.desc(), Event.id.desc())
            .limit(limit)
        )
        if level:
            stmt = stmt.where(Event.level == level)
        if category:
            stmt = stmt.where(Event.entity_type == category)
        if trace_id:
            stmt = stmt.where(Event.trace_id == trace_id)
        if plugin:
            stmt = stmt.where(Event.entity_type == "plugin", Event.entity_id == plugin)
        if batch_id:
            stmt = stmt.where(Event.data["batch_id"].as_string() == batch_id)
        if project_id:
            stmt = stmt.where(Event.data["project_id"].as_string() == project_id)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Event.type.like(term),
                    Event.entity_id.like(term),
                    Event.trace_id.like(term),
                    sa_cast(Event.data, String).like(term),
                )
            )
        rows = (await session.execute(stmt)).scalars().all()
        return cast("list[Event]", list(rows))
