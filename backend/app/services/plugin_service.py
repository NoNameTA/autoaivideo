from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.ws.manager import manager
from app.core.errors import NotFoundError
from app.models.plugin import Plugin
from app.plugins import registry_cache
from app.schemas.plugin import PluginRegister, PluginUpdate


async def _lifecycle(action: str, name: str) -> None:
    await manager.broadcast("activity", {"kind": f"plugin.lifecycle.{action}", "name": name})


class PluginService:
    @staticmethod
    async def list(session: AsyncSession) -> list[Plugin]:
        return list((await session.execute(select(Plugin))).scalars().all())

    @staticmethod
    async def get(session: AsyncSession, name: str) -> Plugin:
        plugin = await session.get(Plugin, name)
        if not plugin:
            raise NotFoundError(f"Plugin '{name}' không tồn tại")
        return plugin

    @staticmethod
    async def register(session: AsyncSession, data: PluginRegister) -> Plugin:
        plugin = await session.get(Plugin, data.name)
        is_new = plugin is None
        if plugin is None:
            plugin = Plugin(name=data.name)
            session.add(plugin)
        plugin.version = data.version
        plugin.capability = data.capability
        plugin.type = data.type
        plugin.manifest = data.manifest
        plugin.config = data.config
        await session.commit()
        await session.refresh(plugin)
        registry_cache.add_capability(data.capability)
        await _lifecycle("installed" if is_new else "updated", plugin.name)
        return plugin

    @staticmethod
    async def update(session: AsyncSession, name: str, data: PluginUpdate) -> Plugin:
        plugin = await PluginService.get(session, name)
        if data.enabled is not None:
            plugin.enabled = data.enabled
        if data.config is not None:
            plugin.config = data.config
        await session.commit()
        await session.refresh(plugin)
        if data.enabled is True:
            await _lifecycle("enabled", name)
        elif data.enabled is False:
            await _lifecycle("disabled", name)
        else:
            await _lifecycle("updated", name)
        return plugin

    @staticmethod
    async def remove(session: AsyncSession, name: str) -> None:
        plugin = await PluginService.get(session, name)
        capability = plugin.capability
        await session.delete(plugin)
        await session.commit()
        registry_cache.discard_capability(capability)
        await _lifecycle("removed", name)

    @staticmethod
    async def get_config_schema(session: AsyncSession, name: str) -> dict:
        plugin = await PluginService.get(session, name)
        return plugin.manifest.get("config_schema", {})
