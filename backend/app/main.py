"""FastAPI entrypoint (SPEC 04 §1, §8)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api.rest import agents, batches, fs, health, jobs, logs, pipelines, plugins, projects
from app.api.ws import agent as ws_agent
from app.api.ws import dashboard as ws_dashboard
from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.db.session import SessionLocal
from app.db.session import engine as db_engine
from app.orchestrator.engine import engine as orchestrator
from app.plugins.loader import sync_plugins
from app.services.pipeline_service import PipelineService

log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    # Kiểm tra kết nối DB lúc khởi động (SPEC 04 §8). Schema do Alembic quản lý (SPEC 10 §5).
    async with db_engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    async with SessionLocal() as session:
        synced = await sync_plugins(session)
        seeded = await PipelineService.sync_builtins(session)
    log.info("Đồng bộ %d plugin, seed %d pipeline built-in", synced, seeded)
    await orchestrator.start()
    log.info("Backend khởi động xong")
    yield
    await orchestrator.stop()
    await db_engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Video Platform V2", version=__version__, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(health.router)
    app.include_router(projects.router)
    app.include_router(batches.router)
    app.include_router(jobs.router)
    app.include_router(agents.router)
    app.include_router(plugins.router)
    app.include_router(pipelines.router)
    app.include_router(logs.router)
    app.include_router(fs.router)
    app.include_router(ws_dashboard.router)
    app.include_router(ws_agent.router)

    return app


app = create_app()
