from __future__ import annotations

from typing import Any

from app.services.langgraph_sdk.client import get_langgraph_client
from fastapi import Request


class LangGraphAssistantsService:
    def __init__(self, request: Request) -> None:
        self._client = get_langgraph_client(request)

    _CREATE_FIELDS = (
        "graph_id",
        "config",
        "context",
        "metadata",
        "assistant_id",
        "if_exists",
        "name",
        "description",
    )

    _SEARCH_FIELDS = (
        "metadata",
        "graph_id",
        "name",
        "limit",
        "offset",
        "sort_by",
        "sort_order",
        "select",
        "response_format",
    )

    _UPDATE_FIELDS = (
        "graph_id",
        "config",
        "context",
        "metadata",
        "name",
        "description",
    )

    _COUNT_FIELDS = (
        "metadata",
        "graph_id",
        "name",
    )

    async def get(self, assistant_id: str) -> Any:
        return await self._client.assistants.get(assistant_id)

    async def create(self, payload: dict[str, Any]) -> Any:
        create_payload = {
            key: payload[key] for key in self._CREATE_FIELDS if key in payload
        }
        return await self._client.assistants.create(**create_payload)

    async def search(self, payload: dict[str, Any]) -> Any:
        search_payload = {
            key: payload[key] for key in self._SEARCH_FIELDS if key in payload
        }
        return await self._client.assistants.search(**search_payload)

    async def update(self, assistant_id: str, payload: dict[str, Any]) -> Any:
        update_payload = {
            key: payload[key] for key in self._UPDATE_FIELDS if key in payload
        }
        return await self._client.assistants.update(assistant_id, **update_payload)

    async def delete(self, assistant_id: str, delete_threads: bool = False) -> Any:
        return await self._client.assistants.delete(
            assistant_id, delete_threads=delete_threads
        )

    async def count(self, payload: dict[str, Any]) -> Any:
        count_payload = {
            key: payload[key] for key in self._COUNT_FIELDS if key in payload
        }
        return await self._client.assistants.count(**count_payload)
