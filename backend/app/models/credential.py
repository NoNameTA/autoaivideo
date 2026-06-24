from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, utcnow
from app.db.ids import new_id


class Credential(Base):
    """Credential Store — bí mật cloud mã hoá (SPEC 10, 11 §3.1). TỔNG QUÁT, không hard-code Google.

    `encrypted_secret` là **đại diện** do Secret Provider sinh (db_store: Fernet token; local_file:
    đường dẫn). API KHÔNG bao giờ trả trường này.
    """

    __tablename__ = "credentials"

    id: Mapped[str] = mapped_column(String(40), primary_key=True, default=lambda: new_id("cred"))
    provider: Mapped[str] = mapped_column(String(60), index=True)
    connection_name: Mapped[str] = mapped_column(String(120))
    authentication_type: Mapped[str] = mapped_column(String(40), default="service_account")
    encrypted_secret: Mapped[str] = mapped_column(Text)
    # metadata phi-bí-mật: scopes, backend (db_store|local_file), expires_at, account_email…
    cred_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
