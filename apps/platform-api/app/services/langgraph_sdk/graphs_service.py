from __future__ import annotations

from typing import Any

from app.services.langgraph_sdk.assistants_service import LangGraphAssistantsService
from app.services.langgraph_sdk.scope_guard import inject_project_metadata
from fastapi import HTTPException, Request


class LangGraphGraphsService:
    _FILTER_FIELDS = (
        "metadata",
        "name",
    )

    def __init__(self, request: Request) -> None:
        self._request = request
        self._assistants_service = LangGraphAssistantsService(request)

    async def search(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized_payload = payload if isinstance(payload, dict) else {}
        limit = self._as_non_negative_int(normalized_payload.get("limit"), default=50)
        offset = self._as_non_negative_int(normalized_payload.get("offset"), default=0)
        query = self._as_string(normalized_payload.get("query")).strip().lower()
        sort_order = (
            self._as_string(normalized_payload.get("sort_order")).strip().lower()
            or "asc"
        )
        if sort_order not in {"asc", "desc"}:
            sort_order = "asc"

        graphs = await self._collect_graphs(normalized_payload)
        if query:
            graphs = [
                item
                for item in graphs
                if query in item["graph_id"].lower()
                or query in self._as_string(item.get("description")).strip().lower()
            ]

        reverse = sort_order == "desc"
        graphs.sort(key=lambda item: item["graph_id"].lower(), reverse=reverse)

        total = len(graphs)
        paginated_items = graphs[offset : offset + limit]
        return {
            "items": paginated_items,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def count(self, payload: dict[str, Any]) -> dict[str, int]:
        normalized_payload = payload if isinstance(payload, dict) else {}
        query = self._as_string(normalized_payload.get("query")).strip().lower()
        graphs = await self._collect_graphs(normalized_payload)
        if query:
            graphs = [
                item
                for item in graphs
                if query in item["graph_id"].lower()
                or query in self._as_string(item.get("description")).strip().lower()
            ]
        return {"count": len(graphs)}

    async def _collect_graphs(self, payload: dict[str, Any]) -> list[dict[str, str]]:
        assistants_payload: dict[str, Any] = {
            key: payload[key]
            for key in self._FILTER_FIELDS
            if key in payload and payload[key] is not None
        }
        assistants_payload = inject_project_metadata(self._request, assistants_payload)
        assistants_payload["select"] = ["graph_id", "description"]

        max_assistants = self._as_non_negative_int(
            payload.get("max_assistants"), default=2000
        )
        page_size = self._as_non_negative_int(
            payload.get("assistants_page_size"), default=200
        )
        if page_size <= 0:
            page_size = 200
        if max_assistants <= 0:
            return []

        graphs_by_id: dict[str, dict[str, str]] = {}
        fetched = 0
        offset = 0

        while fetched < max_assistants:
            page_payload = {
                **assistants_payload,
                "limit": min(page_size, max_assistants - fetched),
                "offset": offset,
            }
            try:
                rows = await self._assistants_service.search(page_payload)
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(
                    status_code=502, detail="langgraph_upstream_unavailable"
                ) from exc
            assistants = self._extract_assistant_rows(rows)
            if not assistants:
                break

            for assistant in assistants:
                graph_id = assistant.get("graph_id")
                if isinstance(graph_id, str) and graph_id:
                    description = self._as_string(assistant.get("description")).strip()
                    existing = graphs_by_id.get(graph_id)
                    if existing is None:
                        graphs_by_id[graph_id] = {
                            "graph_id": graph_id,
                            "description": description,
                        }
                    elif not existing.get("description") and description:
                        existing["description"] = description

            fetched += len(assistants)
            offset += len(assistants)
            if len(assistants) < page_payload["limit"]:
                break

        return list(graphs_by_id.values())

    @staticmethod
    def _extract_assistant_rows(rows: Any) -> list[dict[str, Any]]:
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]

        if isinstance(rows, dict):
            items = rows.get("items")
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]

        return []

    @staticmethod
    def _as_non_negative_int(value: Any, *, default: int) -> int:
        if isinstance(value, bool):
            return default
        if isinstance(value, int):
            return max(0, value)
        if isinstance(value, str) and value.isdigit():
            return int(value)
        return default

    @staticmethod
    def _as_string(value: Any) -> str:
        return value if isinstance(value, str) else ""
