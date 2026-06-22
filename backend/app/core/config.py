"""Cấu hình ứng dụng — đọc từ biến môi trường / .env (SPEC 04 §6)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    data_dir: str = "./data"

    auth_token: str = "change-me-owner-token"
    agent_token: str = "change-me-agent-token"

    max_concurrent_steps: int = 4
    ack_timeout: int = 30
    heartbeat_timeout: int = 120
    engine_tick_seconds: float = 1.0
    retry_base_seconds: int = 2

    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_prod(self) -> bool:
        return self.app_env.lower() == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
