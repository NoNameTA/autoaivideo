"""Xác thực token (SPEC 11 §2). Owner token cho REST/WS; Agent token riêng cho /ws/agent."""

from __future__ import annotations

from app.core.config import Settings
from app.core.errors import UnauthorizedError


def extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None


def verify_owner_token(token: str | None, settings: Settings) -> None:
    if not token or token != settings.auth_token:
        raise UnauthorizedError("Token chủ sở hữu không hợp lệ")


def verify_agent_token(token: str | None, settings: Settings) -> None:
    if not token or token != settings.agent_token:
        raise UnauthorizedError("Token agent không hợp lệ")
