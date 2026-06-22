"""Cấu hình Desktop Agent (SPEC 05 §7)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    backend_ws_url: str = "ws://localhost:8000/ws/agent"
    agent_id: str = "win-pc-01"
    agent_token: str = "change-me-agent-token"
    data_dir: str = "./data"
    chrome_debug_port: int = 9222
    heartbeat_interval: int = 30
    step_timeout: int = 600
    capacity: int = 2


@lru_cache
def get_agent_settings() -> AgentSettings:
    return AgentSettings()
