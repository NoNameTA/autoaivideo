"""Cache capability của plugin (in-memory) để engine phân biệt step plugin vs built-in.

Cập nhật khi sync lúc khởi động + khi đăng ký/gỡ plugin (SPEC 08).
"""

from __future__ import annotations

_caps: set[str] = set()


def set_capabilities(capabilities: list[str]) -> None:
    _caps.clear()
    _caps.update(c for c in capabilities if c)


def add_capability(capability: str) -> None:
    if capability:
        _caps.add(capability)


def discard_capability(capability: str) -> None:
    _caps.discard(capability)


def is_plugin_capability(capability: str | None) -> bool:
    return capability in _caps
