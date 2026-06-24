"""Nạp plugin từ thư mục plugins/<name>/ (SPEC 08 §8).

Đọc manifest.yaml, kiểm tra free-only gate (SPEC 14), import adapter.py theo entrypoint,
trả map capability -> instance Adapter. Plugin xấu/không free -> bỏ qua + log, không làm sập agent.
"""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

import yaml

from agent.sdk import Adapter

log = logging.getLogger("agent")

REQUIRED_FIELDS = ("name", "version", "type", "free", "entrypoint")


class PluginError(Exception):
    pass


def _manifest_capabilities(manifest: dict) -> list[str]:
    """`capabilities` (list, cloud-api) hoặc `capability` (single, plugin thường)."""
    caps = manifest.get("capabilities")
    if isinstance(caps, list) and caps:
        return [str(c) for c in caps]
    single = manifest.get("capability")
    return [str(single)] if single else []


def _load_manifest(plugin_dir: Path) -> dict:
    manifest_path = plugin_dir / "manifest.yaml"
    if not manifest_path.exists():
        raise PluginError(f"thiếu manifest.yaml ở {plugin_dir.name}")
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    missing = [f for f in REQUIRED_FIELDS if f not in manifest]
    if missing:
        raise PluginError(f"{plugin_dir.name}: manifest thiếu trường {missing}")
    if not _manifest_capabilities(manifest):
        raise PluginError(f"{plugin_dir.name}: thiếu capability/capabilities")
    if manifest.get("free") is not True:
        raise PluginError(f"{plugin_dir.name}: free != true (SPEC 14 chặn)")
    return manifest


def _load_adapter(plugin_dir: Path, entrypoint: str) -> Adapter:
    module_name, _, class_name = entrypoint.partition(":")
    file_path = plugin_dir / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"plugin_{plugin_dir.name}", file_path)
    if spec is None or spec.loader is None:
        raise PluginError(f"{plugin_dir.name}: không nạp được {file_path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter_cls = getattr(module, class_name, None)
    if adapter_cls is None or not issubclass(adapter_cls, Adapter):
        raise PluginError(f"{plugin_dir.name}: {class_name} không phải Adapter")
    return adapter_cls()


def load_plugins(plugins_dir: str | Path) -> dict[str, Adapter]:
    base = Path(plugins_dir)
    adapters: dict[str, Adapter] = {}
    if not base.is_dir():
        return adapters
    for plugin_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        if not (plugin_dir / "manifest.yaml").exists():
            continue
        try:
            manifest = _load_manifest(plugin_dir)
            adapter = _load_adapter(plugin_dir, manifest["entrypoint"])
            caps = _manifest_capabilities(manifest)
            # Adapter phải khai đúng các capability nó phục vụ (single qua `capability`,
            # nhiều qua `capabilities`).
            declared = set(adapter.capabilities)
            if adapter.capability:
                declared.add(adapter.capability)
            if not set(caps).issubset(declared):
                raise PluginError(
                    f"{plugin_dir.name}: adapter không khai đủ capability {caps} (có {declared})"
                )
            for cap in caps:
                adapters[cap] = adapter  # cùng 1 instance phục vụ nhiều capability
            log.info("Nạp plugin %s (capabilities=%s)", manifest["name"], caps)
        except Exception as e:  # noqa: BLE001 - plugin lỗi không làm sập agent
            log.warning("Bỏ qua plugin %s: %s", plugin_dir.name, e)
    return adapters
