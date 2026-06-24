"""Cấu hình ứng dụng — đọc từ biến môi trường / .env (SPEC 04 §6)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "dev"
    database_url: str = "sqlite+aiosqlite:///./data/app.db"
    data_dir: str = "./data"

    auth_token: str = "change-me-owner-token"
    agent_token: str = "change-me-agent-token"

    # Secret Provider (SPEC 11 §3.5). Có MASTER_KEY (Fernet urlsafe-base64 32 byte) -> db_store
    # mã hoá; trống (dev) -> local_file. KHÔNG hard-code khoá; đặt qua env.
    master_key: str = ""
    # Thư mục chứa file bí mật cục bộ (local_file provider) — gitignored.
    secrets_dir: str = "./.secrets"

    max_concurrent_steps: int = 4
    ack_timeout: int = 30
    heartbeat_timeout: int = 120
    engine_tick_seconds: float = 1.0
    retry_base_seconds: int = 2

    # NoDecode: không để pydantic-settings JSON-decode env -> để validator tự tách chuỗi "a,b".
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

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
