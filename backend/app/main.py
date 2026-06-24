"""FastAPI entrypoint (SPEC 04 §1, §8)."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import __version__
from app.api.rest import (
    agents,
    batches,
    connections,
    credentials,
    external_apps,
    fs,
    health,
    jobs,
    logs,
    pipelines,
    plugins,
    projects,
    stats,
    video_sources,
)
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
        # Tự tạo credential Google từ gsa.json (nếu có) -> người dùng khỏi tự cấu hình.
        from app.services.credential_service import CredentialService

        cred = await CredentialService.ensure_default_google(session)
    log.info(
        "Đồng bộ %d plugin, seed %d pipeline built-in, credential Google: %s",
        synced, seeded, "có" if cred else "chưa (thiếu gsa.json)",
    )
    await orchestrator.start()
    from app.services.auto_sync import scheduler as auto_sync_scheduler

    await auto_sync_scheduler.start()
    log.info("Backend khởi động xong")
    yield
    await auto_sync_scheduler.stop()
    await orchestrator.stop()
    await db_engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="AI Video Platform V2", version=__version__, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # Cho phép mọi origin localhost/127.0.0.1 (mọi cổng) — tránh kẹt CORS khi chạy local
        # bằng địa chỉ khác cổng cấu hình (SPEC 04 §6). Production vẫn dùng cors_origins tường minh.
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
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
    app.include_router(stats.router)
    app.include_router(external_apps.router)
    app.include_router(credentials.router)
    app.include_router(connections.router)
    app.include_router(video_sources.router)
    app.include_router(fs.router)
    app.include_router(ws_dashboard.router)
    app.include_router(ws_agent.router)

    _mount_frontend(app)
    return app


def _mount_frontend(app: FastAPI) -> None:
    """Phục vụ web (frontend/dist) NGAY TỪ backend -> 1 địa chỉ duy nhất, same-origin (hết CORS).

    Chỉ bật khi đã `npm run build` (có frontend/dist). SPA fallback: route con (vd /video-sources)
    trả index.html để React Router xử lý. KHÔNG đụng /api, /ws, /health (đã match ở trên).
    """
    from pathlib import Path

    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    index = dist / "index.html"
    if not index.is_file():
        log.warning("Chưa có frontend/dist (chạy 'npm run build') — backend chỉ phục vụ API")
        return
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=str(dist / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa(full_path: str) -> FileResponse:
        candidate = dist / full_path
        if full_path and candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(index))  # SPA fallback

    log.info("Phục vụ frontend từ %s", dist)


app = create_app()
