"""Health & info endpoints (SPEC 04 §2)."""

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.api.deps import SessionDep
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/ready")
async def ready(session: SessionDep) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.get("/api/v1/info")
async def info() -> dict:
    s = get_settings()
    return {
        "name": "AI Video Platform V2",
        "version": __version__,
        "env": s.app_env,
        "max_concurrent_steps": s.max_concurrent_steps,
    }
