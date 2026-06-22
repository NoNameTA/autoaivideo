"""Nạp pipeline template (SPEC 02 §4). Lưu dạng JSON cạnh module này."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.errors import NotFoundError

_DIR = Path(__file__).parent / "pipelines"


@lru_cache
def _load_all() -> dict[str, dict]:
    templates: dict[str, dict] = {}
    for f in _DIR.glob("*.json"):
        data = json.loads(f.read_text(encoding="utf-8"))
        templates[data["name"]] = data
    return templates


def get_template_steps(name: str) -> list[dict]:
    template = _load_all().get(name)
    if not template:
        raise NotFoundError(f"Pipeline template '{name}' không tồn tại")
    return template["steps"]


def list_templates() -> list[str]:
    return sorted(_load_all().keys())
