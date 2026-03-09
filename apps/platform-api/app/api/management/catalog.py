from __future__ import annotations

from typing import Any

from app.api.management.common import require_db_session_factory
from app.db.access import (
    list_runtime_graph_catalog_items,
    list_runtime_model_catalog_items,
    list_runtime_tool_catalog_items,
)
from app.db.session import session_scope
from app.services.runtime_catalog_sync import RuntimeCatalogSyncService
from fastapi import APIRouter, Request

router = APIRouter(prefix="/catalog", tags=["management-catalog"])


def _runtime_id(request: Request) -> str:
    return request.app.state.settings.langgraph_upstream_url.rstrip("/")


def _serialize_model(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "runtime_id": row.runtime_id,
        "model_id": row.model_key,
        "display_name": row.display_name or row.model_key,
        "is_default": row.is_default_runtime,
        "sync_status": row.sync_status,
        "last_seen_at": row.last_seen_at,
        "last_synced_at": row.last_synced_at,
    }


def _serialize_tool(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "runtime_id": row.runtime_id,
        "tool_key": row.tool_key,
        "name": row.name,
        "source": row.source or "",
        "description": row.description or "",
        "sync_status": row.sync_status,
        "last_seen_at": row.last_seen_at,
        "last_synced_at": row.last_synced_at,
    }


def _serialize_graph(row: Any) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "runtime_id": row.runtime_id,
        "graph_id": row.graph_key,
        "display_name": row.display_name or row.graph_key,
        "description": row.description or "",
        "source_type": row.source_type,
        "sync_status": row.sync_status,
        "last_seen_at": row.last_seen_at,
        "last_synced_at": row.last_synced_at,
    }


@router.get("/models")
async def list_catalog_models(request: Request) -> dict[str, Any]:
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        rows = list_runtime_model_catalog_items(
            session, runtime_id=_runtime_id(request)
        )
    items = [_serialize_model(row) for row in rows]
    return {
        "count": len(items),
        "items": items,
        "last_synced_at": max(
            (item["last_synced_at"] for item in items if item["last_synced_at"]),
            default=None,
        ),
    }


@router.post("/models/refresh")
async def refresh_catalog_models(request: Request) -> dict[str, Any]:
    service = RuntimeCatalogSyncService(request)
    result = await service.sync_models_from_runtime()
    return {"ok": True, **result}


@router.get("/tools")
async def list_catalog_tools(request: Request) -> dict[str, Any]:
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        rows = list_runtime_tool_catalog_items(session, runtime_id=_runtime_id(request))
    items = [_serialize_tool(row) for row in rows]
    return {
        "count": len(items),
        "items": items,
        "last_synced_at": max(
            (item["last_synced_at"] for item in items if item["last_synced_at"]),
            default=None,
        ),
    }


@router.post("/tools/refresh")
async def refresh_catalog_tools(request: Request) -> dict[str, Any]:
    service = RuntimeCatalogSyncService(request)
    result = await service.sync_tools_from_runtime()
    return {"ok": True, **result}


@router.get("/graphs")
async def list_catalog_graphs(request: Request) -> dict[str, Any]:
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        rows = list_runtime_graph_catalog_items(
            session, runtime_id=_runtime_id(request)
        )
    items = [_serialize_graph(row) for row in rows]
    return {
        "count": len(items),
        "items": items,
        "last_synced_at": max(
            (item["last_synced_at"] for item in items if item["last_synced_at"]),
            default=None,
        ),
    }


@router.post("/graphs/refresh")
async def refresh_catalog_graphs(request: Request) -> dict[str, Any]:
    service = RuntimeCatalogSyncService(request)
    result = await service.sync_graphs_from_runtime()
    return {"ok": True, **result}
