from __future__ import annotations

from typing import Any

from app.services.langgraph_sdk.client import get_langgraph_client
from fastapi import Request


class LangGraphThreadsService:
    def __init__(self, request: Request) -> None:
        self._client = get_langgraph_client(request)

    _CREATE_FIELDS = (
        "metadata",
        "thread_id",
        "if_exists",
        "supersteps",
        "graph_id",
        "ttl",
    )

    _SEARCH_FIELDS = (
        "metadata",
        "values",
        "ids",
        "status",
        "limit",
        "offset",
        "sort_by",
        "sort_order",
        "select",
        "extract",
    )

    _STATE_FIELDS = (
        "subgraphs",
        "checkpoint_id",
    )

    _HISTORY_FIELDS = (
        "limit",
        "before",
        "metadata",
        "checkpoint",
    )

    _COUNT_FIELDS = (
        "metadata",
        "values",
        "status",
    )

    _PRUNE_FIELDS = (
        "thread_ids",
        "strategy",
    )

    _UPDATE_FIELDS = (
        "metadata",
        "ttl",
    )

    _UPDATE_STATE_FIELDS = (
        "values",
        "as_node",
        "checkpoint",
        "checkpoint_id",
    )

    async def get(self, thread_id: str) -> Any:
        return await self._client.threads.get(thread_id)

    async def create(self, payload: dict[str, Any] | None = None) -> Any:
        create_payload = {
            key: payload[key]
            for key in self._CREATE_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.threads.create(**create_payload)

    async def search(self, payload: dict[str, Any]) -> Any:
        search_payload = {
            key: payload[key] for key in self._SEARCH_FIELDS if key in payload
        }
        return await self._client.threads.search(**search_payload)

    async def get_state(
        self, thread_id: str, payload: dict[str, Any] | None = None
    ) -> Any:
        state_payload = {
            key: payload[key]
            for key in self._STATE_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.threads.get_state(thread_id, **state_payload)

    async def get_history(
        self, thread_id: str, payload: dict[str, Any] | None = None
    ) -> Any:
        history_payload = {
            key: payload[key]
            for key in self._HISTORY_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.threads.get_history(thread_id, **history_payload)

    async def count(self, payload: dict[str, Any]) -> Any:
        count_payload = {
            key: payload[key] for key in self._COUNT_FIELDS if key in payload
        }
        return await self._client.threads.count(**count_payload)

    async def prune(self, payload: dict[str, Any]) -> Any:
        prune_payload = {
            key: payload[key] for key in self._PRUNE_FIELDS if key in payload
        }
        return await self._client.threads.prune(**prune_payload)

    async def update(self, thread_id: str, payload: dict[str, Any]) -> Any:
        update_payload = {
            key: payload[key] for key in self._UPDATE_FIELDS if key in payload
        }
        return await self._client.threads.update(thread_id, **update_payload)

    async def delete(self, thread_id: str) -> Any:
        return await self._client.threads.delete(thread_id)

    async def copy(self, thread_id: str) -> Any:
        return await self._client.threads.copy(thread_id)

    async def update_state(self, thread_id: str, payload: dict[str, Any]) -> Any:
        update_state_payload = {
            key: payload[key] for key in self._UPDATE_STATE_FIELDS if key in payload
        }
        return await self._client.threads.update_state(
            thread_id, **update_state_payload
        )

    async def get_state_at_checkpoint(self, thread_id: str, checkpoint_id: str) -> Any:
        return await self._client.threads.get_state(
            thread_id, checkpoint_id=checkpoint_id
        )
