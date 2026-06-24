from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CredentialCreate(BaseModel):
    """Tạo credential. Material write-only — chọn 1 trong secret_path/secret_inline."""

    provider: str = Field(min_length=1, max_length=60)
    connection_name: str = Field(min_length=1, max_length=120)
    authentication_type: str = "service_account"
    scopes: list[str] = []
    # local_file: đường dẫn file bí mật (gitignored). db_store: material thô (cần MASTER_KEY).
    secret_path: str | None = None
    secret_inline: str | None = None


class CredentialOut(BaseModel):
    """CHỈ metadata — KHÔNG bao giờ trả `encrypted_secret`/material thật (SPEC 11 §3.1)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    connection_name: str
    authentication_type: str
    metadata: dict = Field(validation_alias="cred_metadata")
    status: str
    created_at: datetime
    updated_at: datetime
    last_used_at: datetime | None
