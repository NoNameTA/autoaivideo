"""Contract test cho Plugin SDK + các plugin trong plugins/ (SPEC 08 §9, 14, 15 §3).

Kiểm tra manifest, free-only gate, JSON Schema, adapter subclass + lifecycle, loader nạp đủ.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import yaml

from agent.plugin_loader import load_plugins
from agent.sdk import Adapter

PLUGINS_DIR = Path(__file__).resolve().parents[2] / "plugins"
REQUIRED = (
    "name",
    "version",
    "type",
    "free",
    "license",
    "entrypoint",
    "config_schema",
)


def _plugin_dirs() -> list[Path]:
    return [p for p in sorted(PLUGINS_DIR.iterdir()) if (p / "manifest.yaml").exists()]


def _manifest(plugin_dir: Path) -> dict:
    return yaml.safe_load((plugin_dir / "manifest.yaml").read_text(encoding="utf-8"))


def _caps(m: dict) -> list[str]:
    """`capabilities` (list, cloud-api) hoặc `capability` (single, plugin thường)."""
    caps = m.get("capabilities")
    if isinstance(caps, list) and caps:
        return [str(c) for c in caps]
    return [str(m["capability"])] if m.get("capability") else []


def test_plugins_present() -> None:
    names = {p.name for p in _plugin_dirs()}
    assert {"ffmpeg", "yt_dlp", "chrome"} <= names


def test_manifest_contract() -> None:
    for plugin_dir in _plugin_dirs():
        m = _manifest(plugin_dir)
        for field in REQUIRED:
            assert field in m, f"{plugin_dir.name} thiếu '{field}'"
        # capability (single) hoặc capabilities (list cloud-api)
        assert _caps(m), f"{plugin_dir.name} thiếu capability/capabilities"
        # Cổng free-only (SPEC 14)
        assert m["free"] is True, f"{plugin_dir.name} không free"
        # JSON Schema hợp lệ + là object (SPEC 08 §7)
        schema_path = plugin_dir / m["config_schema"]
        assert schema_path.exists(), f"{plugin_dir.name} thiếu {m['config_schema']}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        assert schema.get("type") == "object"


def test_adapter_contract() -> None:
    for plugin_dir in _plugin_dirs():
        m = _manifest(plugin_dir)
        module_name, _, class_name = m["entrypoint"].partition(":")
        spec = importlib.util.spec_from_file_location(
            f"contract_{plugin_dir.name}", plugin_dir / f"{module_name}.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        adapter_cls = getattr(module, class_name)
        assert issubclass(adapter_cls, Adapter), f"{plugin_dir.name}: không phải Adapter"
        instance = adapter_cls()
        declared = set(instance.capabilities) | (
            {instance.capability} if instance.capability else set()
        )
        assert set(_caps(m)) <= declared, f"{plugin_dir.name}: adapter thiếu capability"
        assert callable(getattr(instance, "run", None))


def test_loader_registers_capabilities() -> None:
    adapters = load_plugins(PLUGINS_DIR)
    caps = set(adapters.keys())
    assert {"video.ffmpeg", "media.download", "web.cdp"} <= caps
    # cloud-api: 1 adapter đăng ký dưới nhiều capability.
    assert {"cloud.google_sheets.read", "cloud.google_sheets.write"} <= caps
