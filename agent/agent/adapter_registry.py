"""Gộp adapter built-in + plugin nạp từ thư mục plugins/ (SPEC 08 §8)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from agent.adapters.cli_run import CliRunAdapter
from agent.plugin_loader import load_plugins
from agent.sdk import Adapter

# Adapter built-in của agent.
_BUILTIN: dict[str, Adapter] = {CliRunAdapter.capability: CliRunAdapter()}


def _default_plugins_dir() -> Path:
    # repo_root/plugins (agent/agent/adapter_registry.py -> lên 3 cấp = repo root).
    return Path(__file__).resolve().parents[2] / "plugins"


@lru_cache
def get_adapters(plugins_dir: str | None = None) -> dict[str, Adapter]:
    base = Path(plugins_dir) if plugins_dir else _default_plugins_dir()
    adapters: dict[str, Adapter] = dict(_BUILTIN)
    adapters.update(load_plugins(base))
    return adapters


def capabilities(plugins_dir: str | None = None) -> list[str]:
    return sorted(get_adapters(plugins_dir).keys())
