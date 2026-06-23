"""External Apps (SPEC 06): app ngoài bọc bởi Adapter (plugin). Trang này là view vận
hành theo loại tích hợp + **trạng thái kết nối** (agent online có capability) + **test kết nối**.

Khác Plugin Manager (lifecycle install/enable/remove): ở đây tập trung kết nối & sẵn sàng chạy.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.models.plugin import Plugin
from app.orchestrator.agent_registry import registry


def _connection(capability: str, enabled: bool) -> dict:
    """Trạng thái kết nối suy từ agent registry live (socket đang mở)."""
    if not enabled:
        return {"status": "disabled", "online_agents": [], "capacity_free": False}
    agents = [c.agent_id for c in registry.online_for(capability)]
    if not agents:
        return {"status": "no_agent", "online_agents": [], "capacity_free": False}
    return {
        "status": "connected",
        "online_agents": agents,
        "capacity_free": registry.has_free_slot(capability),
    }


def _to_external_app(p: Plugin) -> dict:
    manifest = p.manifest or {}
    return {
        "name": p.name,
        "capability": p.capability,
        "type": p.type,
        "version": p.version,
        "enabled": p.enabled,
        "free": bool(manifest.get("free", True)),
        "license": manifest.get("license"),
        "source_url": manifest.get("source_url"),
        "connection": _connection(p.capability, p.enabled),
    }


class ExternalAppService:
    @staticmethod
    async def list(session: AsyncSession) -> list[dict]:
        stmt = select(Plugin).order_by(Plugin.type, Plugin.name)
        plugins = (await session.execute(stmt)).scalars()
        return [_to_external_app(p) for p in plugins]

    @staticmethod
    async def test(session: AsyncSession, name: str) -> dict:
        """Test kết nối THẬT: app có sẵn sàng được điều phối ngay bây giờ không?

        Kiểm tra: plugin tồn tại → free policy → đang bật → có agent online hỗ trợ
        capability (+ còn slot). Không mock — phản ánh khả năng dispatch thực tế.
        """
        plugin = await session.get(Plugin, name)
        if plugin is None:
            raise NotFoundError(f"External app '{name}' không tồn tại")

        manifest = plugin.manifest or {}
        if not bool(manifest.get("free", True)):
            return {
                "ok": False,
                "reason": "Vi phạm chính sách phần mềm miễn phí (free=false)",
                "agents": [],
            }
        if not plugin.enabled:
            return {"ok": False, "reason": "Adapter đang tắt — bật trước khi test", "agents": []}

        agents = [c.agent_id for c in registry.online_for(plugin.capability)]
        if not agents:
            return {
                "ok": False,
                "reason": f"Chưa có agent online hỗ trợ capability '{plugin.capability}'",
                "agents": [],
            }
        if not registry.has_free_slot(plugin.capability):
            return {
                "ok": False,
                "reason": f"Agent có capability '{plugin.capability}' nhưng đã hết slot",
                "agents": agents,
            }
        return {
            "ok": True,
            "reason": f"Sẵn sàng — agent {', '.join(agents)} hỗ trợ '{plugin.capability}'",
            "agents": agents,
        }
