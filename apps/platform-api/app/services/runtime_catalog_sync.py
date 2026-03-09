from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from app.db.access import (
    mark_missing_runtime_catalog_graphs_deleted,
    mark_missing_runtime_catalog_models_deleted,
    mark_missing_runtime_catalog_tools_deleted,
    upsert_runtime_graph_catalog_items,
    upsert_runtime_model_catalog_items,
    upsert_runtime_tool_catalog_items,
)
from app.db.session import session_scope
from fastapi import HTTPException, Request


class RuntimeCatalogSyncService:
    def __init__(self, request: Request) -> None:
        self._request = request
        self._client: httpx.AsyncClient = request.app.state.client
        self._settings = request.app.state.settings
        self._session_factory = request.app.state.db_session_factory
        self._runtime_id = self._settings.langgraph_upstream_url.rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {"accept": "application/json"}
        for key in ("authorization", "x-tenant-id", "x-project-id", "x-request-id"):
            value = self._request.headers.get(key)
            if value:
                headers[key] = value
        request_id = getattr(self._request.state, "request_id", None)
        if request_id and "x-request-id" not in headers:
            headers["x-request-id"] = str(request_id)
        if self._settings.langgraph_upstream_api_key:
            headers["x-api-key"] = self._settings.langgraph_upstream_api_key
        return headers

    async def _get_json(self, path: str) -> Any:
        url = f"{self._runtime_id}{path}"
        try:
            response = await self._client.get(url, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504, detail=f"runtime_catalog_timeout: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail=f"runtime_catalog_unavailable: {exc}"
            ) from exc
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise HTTPException(status_code=response.status_code, detail=detail)
        return response.json()

    async def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        url = f"{self._runtime_id}{path}"
        try:
            response = await self._client.post(
                url, headers=self._headers(), json=payload
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504, detail=f"runtime_catalog_timeout: {exc}"
            ) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail=f"runtime_catalog_unavailable: {exc}"
            ) from exc
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise HTTPException(status_code=response.status_code, detail=detail)
        return response.json()

    async def sync_models_from_runtime(self) -> dict[str, Any]:
        payload = await self._get_json("/internal/capabilities/models")
        models = payload.get("models") if isinstance(payload, dict) else None
        normalized = [item for item in (models or []) if isinstance(item, dict)]
        synced_at = datetime.now(timezone.utc)
        active_keys = {
            str(item.get("model_id") or "").strip()
            for item in normalized
            if item.get("model_id")
        }
        with session_scope(self._session_factory) as session:
            upsert_runtime_model_catalog_items(
                session,
                runtime_id=self._runtime_id,
                items=normalized,
                synced_at=synced_at,
            )
            mark_missing_runtime_catalog_models_deleted(
                session,
                runtime_id=self._runtime_id,
                active_keys=active_keys,
                synced_at=synced_at,
            )
        return {"count": len(normalized), "last_synced_at": synced_at.isoformat()}

    async def sync_tools_from_runtime(self) -> dict[str, Any]:
        payload = await self._get_json("/internal/capabilities/tools")
        tools = payload.get("tools") if isinstance(payload, dict) else None
        normalized = [item for item in (tools or []) if isinstance(item, dict)]
        synced_at = datetime.now(timezone.utc)
        active_keys = {
            f"{str(item.get('source') or '').strip()}:{str(item.get('name') or '').strip()}".lstrip(
                ":"
            )
            for item in normalized
            if item.get("name")
        }
        with session_scope(self._session_factory) as session:
            upsert_runtime_tool_catalog_items(
                session,
                runtime_id=self._runtime_id,
                items=normalized,
                synced_at=synced_at,
            )
            mark_missing_runtime_catalog_tools_deleted(
                session,
                runtime_id=self._runtime_id,
                active_keys=active_keys,
                synced_at=synced_at,
            )
        return {"count": len(normalized), "last_synced_at": synced_at.isoformat()}

    async def sync_graphs_from_runtime(self) -> dict[str, Any]:
        graph_map: dict[str, dict[str, Any]] = {}
        offset = 0
        limit = 200
        while True:
            payload = {
                "limit": limit,
                "offset": offset,
                "select": ["graph_id", "description"],
            }
            response = await self._post_json("/assistants/search", payload)
            if isinstance(response, list):
                rows = [item for item in response if isinstance(item, dict)]
            elif isinstance(response, dict) and isinstance(response.get("items"), list):
                rows = [item for item in response["items"] if isinstance(item, dict)]
            else:
                rows = []
            if not rows:
                break
            for item in rows:
                graph_id = str(item.get("graph_id") or "").strip()
                if not graph_id:
                    continue
                existing = graph_map.get(graph_id)
                description = str(item.get("description") or "").strip()
                if existing is None:
                    graph_map[graph_id] = {
                        "graph_id": graph_id,
                        "display_name": graph_id,
                        "description": description,
                    }
                elif not existing.get("description") and description:
                    existing["description"] = description
            if len(rows) < limit:
                break
            offset += len(rows)
        synced_at = datetime.now(timezone.utc)
        items = list(graph_map.values())
        active_keys = {item["graph_id"] for item in items}
        with session_scope(self._session_factory) as session:
            upsert_runtime_graph_catalog_items(
                session,
                runtime_id=self._runtime_id,
                items=items,
                synced_at=synced_at,
                source_type="assistant_search",
            )
            mark_missing_runtime_catalog_graphs_deleted(
                session,
                runtime_id=self._runtime_id,
                active_keys=active_keys,
                synced_at=synced_at,
            )
        return {"count": len(items), "last_synced_at": synced_at.isoformat()}
