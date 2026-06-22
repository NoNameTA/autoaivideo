"""Quét thư mục plugins/ -> đồng bộ registry vào DB (SPEC 08 §8).

Backend không nạp code adapter (adapter chạy ở agent) — chỉ đọc manifest + config schema để
hiển thị trên Plugin Manager và phục vụ /plugins/{name}/schema. Áp cổng free-only (SPEC 14).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plugin import Plugin

log = logging.getLogger("app")


def _plugins_dir() -> Path:
    # backend/app/plugins/loader.py -> parents[3] = gốc repo
    return Path(__file__).resolve().parents[3] / "plugins"


def discover() -> list[dict]:
    base = _plugins_dir()
    manifests: list[dict] = []
    if not base.is_dir():
        return manifests
    for plugin_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        manifest_path = plugin_dir / "manifest.yaml"
        if not manifest_path.exists():
            continue
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        schema_file = manifest.get("config_schema")
        if isinstance(schema_file, str):
            schema_path = plugin_dir / schema_file
            if schema_path.exists():
                manifest["config_schema"] = json.loads(schema_path.read_text(encoding="utf-8"))
        manifests.append(manifest)
    return manifests


async def sync_plugins(session: AsyncSession) -> int:
    count = 0
    for manifest in discover():
        if manifest.get("free") is not True:
            log.warning("Bỏ qua plugin không free: %s", manifest.get("name"))
            continue
        name = manifest.get("name")
        if not name:
            continue
        plugin = await session.get(Plugin, name)
        if plugin is None:
            plugin = Plugin(name=name, enabled=False, config={})
            session.add(plugin)
        # Giữ nguyên enabled + config do người dùng đặt; chỉ cập nhật metadata.
        plugin.version = str(manifest.get("version", ""))
        plugin.capability = manifest.get("capability", "")
        plugin.type = manifest.get("type", "")
        plugin.manifest = manifest
        count += 1
    await session.commit()
    return count
