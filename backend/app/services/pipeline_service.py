from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.models.pipeline import Pipeline
from app.orchestrator.templates import get_template_steps, list_templates
from app.schemas.pipeline import PipelineCreate, PipelineUpdate


class PipelineService:
    @staticmethod
    async def list(session: AsyncSession) -> list[Pipeline]:
        rows = (await session.execute(select(Pipeline).order_by(Pipeline.name))).scalars().all()
        return list(rows)

    @staticmethod
    async def get(session: AsyncSession, name: str) -> Pipeline:
        pipeline = (
            await session.execute(select(Pipeline).where(Pipeline.name == name))
        ).scalar_one_or_none()
        if pipeline is None:
            raise NotFoundError(f"Pipeline '{name}' không tồn tại")
        return pipeline

    @staticmethod
    async def create(session: AsyncSession, data: PipelineCreate) -> Pipeline:
        existing = (
            await session.execute(select(Pipeline).where(Pipeline.name == data.name))
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError(f"Pipeline '{data.name}' đã tồn tại")
        pipeline = Pipeline(
            name=data.name,
            description=data.description,
            steps=[s.model_dump() for s in data.steps],
            builtin=False,
        )
        session.add(pipeline)
        await session.commit()
        await session.refresh(pipeline)
        return pipeline

    @staticmethod
    async def update(session: AsyncSession, name: str, data: PipelineUpdate) -> Pipeline:
        pipeline = await PipelineService.get(session, name)
        if data.description is not None:
            pipeline.description = data.description
        if data.steps is not None:
            pipeline.steps = [s.model_dump() for s in data.steps]
        await session.commit()
        await session.refresh(pipeline)
        return pipeline

    @staticmethod
    async def delete(session: AsyncSession, name: str) -> None:
        pipeline = await PipelineService.get(session, name)
        await session.delete(pipeline)
        await session.commit()

    @staticmethod
    async def get_steps(session: AsyncSession, name: str) -> list[dict]:
        """Lấy step để tạo batch: ưu tiên DB, fallback template JSON built-in (SPEC 02 §4)."""
        pipeline = (
            await session.execute(select(Pipeline).where(Pipeline.name == name))
        ).scalar_one_or_none()
        if pipeline is not None:
            return list(pipeline.steps)
        return get_template_steps(name)  # NotFoundError nếu không có

    @staticmethod
    async def sync_builtins(session: AsyncSession) -> int:
        """Seed pipeline built-in từ file JSON vào DB (insert-if-missing, không ghi đè user)."""
        count = 0
        for name in list_templates():
            existing = (
                await session.execute(select(Pipeline).where(Pipeline.name == name))
            ).scalar_one_or_none()
            if existing is not None:
                continue
            steps = [
                {"step_key": s["step_key"], "adapter": s["adapter"], "config": s.get("config", {})}
                for s in get_template_steps(name)
            ]
            session.add(Pipeline(name=name, description="(built-in)", steps=steps, builtin=True))
            count += 1
        await session.commit()
        return count
