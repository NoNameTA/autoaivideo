from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import SessionDep, require_owner
from app.schemas.plugin import PluginOut, PluginRegister, PluginSchema, PluginUpdate
from app.services.plugin_service import PluginService

router = APIRouter(
    prefix="/api/v1/plugins", tags=["plugins"], dependencies=[Depends(require_owner)]
)


@router.get("", response_model=list[PluginOut])
async def list_plugins(session: SessionDep) -> list[PluginOut]:
    return await PluginService.list(session)  # type: ignore[return-value]


@router.post("", response_model=PluginOut, status_code=status.HTTP_201_CREATED)
async def register_plugin(data: PluginRegister, session: SessionDep) -> PluginOut:
    return await PluginService.register(session, data)  # type: ignore[return-value]


@router.get("/{name}/schema", response_model=PluginSchema)
async def get_plugin_schema(name: str, session: SessionDep) -> PluginSchema:
    schema = await PluginService.get_config_schema(session, name)
    return PluginSchema(name=name, schema_=schema)


@router.patch("/{name}", response_model=PluginOut)
async def update_plugin(name: str, data: PluginUpdate, session: SessionDep) -> PluginOut:
    return await PluginService.update(session, name, data)  # type: ignore[return-value]


@router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_plugin(name: str, session: SessionDep):
    await PluginService.remove(session, name)
