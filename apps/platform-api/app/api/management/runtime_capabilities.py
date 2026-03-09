from __future__ import annotations

from typing import Any

from app.api.management.catalog import list_catalog_models, list_catalog_tools
from fastapi import APIRouter, Request

router = APIRouter(prefix="/runtime", tags=["management-runtime"])


@router.get("/models")
async def list_runtime_models(request: Request) -> Any:
    payload = await list_catalog_models(request)
    return {
        "count": payload["count"],
        "models": payload["items"],
        "last_synced_at": payload["last_synced_at"],
    }


@router.get("/tools")
async def list_runtime_tools(request: Request) -> Any:
    payload = await list_catalog_tools(request)
    return {
        "count": payload["count"],
        "tools": payload["items"],
        "last_synced_at": payload["last_synced_at"],
    }
