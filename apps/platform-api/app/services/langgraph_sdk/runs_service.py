from __future__ import annotations

from typing import Any

from app.services.langgraph_sdk.client import get_langgraph_client
from fastapi import Request


class LangGraphRunsService:
    _CREATE_FIELDS = (
        "input",
        "command",
        "stream_mode",
        "stream_subgraphs",
        "stream_resumable",
        "metadata",
        "config",
        "context",
        "checkpoint",
        "checkpoint_id",
        "checkpoint_during",
        "interrupt_before",
        "interrupt_after",
        "webhook",
        "multitask_strategy",
        "if_not_exists",
        "on_completion",
        "after_seconds",
        "durability",
    )

    _STREAM_FIELDS = _CREATE_FIELDS + (
        "feedback_keys",
        "on_disconnect",
    )

    _WAIT_FIELDS = _CREATE_FIELDS + (
        "raise_error",
        "on_disconnect",
    )

    _CANCEL_FIELDS = (
        "wait",
        "action",
    )

    _BULK_CANCEL_FIELDS = (
        "thread_id",
        "run_ids",
        "status",
        "action",
    )

    _LIST_FIELDS = (
        "limit",
        "offset",
        "status",
        "select",
    )

    _CRON_CREATE_FIELDS = (
        "schedule",
        "input",
        "metadata",
        "config",
        "context",
        "checkpoint_during",
        "interrupt_before",
        "interrupt_after",
        "webhook",
        "on_run_completed",
        "multitask_strategy",
        "end_time",
        "enabled",
        "stream_mode",
        "stream_subgraphs",
        "stream_resumable",
        "durability",
    )

    _CRON_SEARCH_FIELDS = (
        "assistant_id",
        "thread_id",
        "enabled",
        "limit",
        "offset",
        "sort_by",
        "sort_order",
        "select",
    )

    _CRON_COUNT_FIELDS = (
        "assistant_id",
        "thread_id",
    )

    _CRON_UPDATE_FIELDS = (
        "schedule",
        "end_time",
        "input",
        "metadata",
        "config",
        "context",
        "webhook",
        "interrupt_before",
        "interrupt_after",
        "on_run_completed",
        "enabled",
        "stream_mode",
        "stream_subgraphs",
        "stream_resumable",
        "durability",
    )

    _JOIN_STREAM_FIELDS = (
        "cancel_on_disconnect",
        "stream_mode",
        "last_event_id",
    )

    def __init__(self, request: Request) -> None:
        self._client = get_langgraph_client(request)

    async def create(self, thread_id: str, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        create_payload = {
            key: payload[key] for key in self._CREATE_FIELDS if key in payload
        }
        return await self._client.runs.create(thread_id, assistant_id, **create_payload)

    async def create_global(self, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        create_payload = {
            key: payload[key] for key in self._CREATE_FIELDS if key in payload
        }
        return await self._client.runs.create(None, assistant_id, **create_payload)

    async def stream(self, thread_id: str, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        stream_payload = {
            key: payload[key] for key in self._STREAM_FIELDS if key in payload
        }
        return self._client.runs.stream(thread_id, assistant_id, **stream_payload)

    async def stream_global(self, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        stream_payload = {
            key: payload[key] for key in self._STREAM_FIELDS if key in payload
        }
        return self._client.runs.stream(None, assistant_id, **stream_payload)

    async def wait(self, thread_id: str, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        wait_payload = {
            key: payload[key] for key in self._WAIT_FIELDS if key in payload
        }
        return await self._client.runs.wait(thread_id, assistant_id, **wait_payload)

    async def wait_global(self, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        wait_payload = {
            key: payload[key] for key in self._WAIT_FIELDS if key in payload
        }
        return await self._client.runs.wait(None, assistant_id, **wait_payload)

    async def create_batch(self, payloads: list[dict[str, Any]]) -> Any:
        return await self._client.runs.create_batch(payloads)

    async def get(self, thread_id: str, run_id: str) -> Any:
        return await self._client.runs.get(thread_id, run_id)

    async def cancel(
        self, thread_id: str, run_id: str, payload: dict[str, Any] | None = None
    ) -> Any:
        cancel_payload = {
            key: payload[key]
            for key in self._CANCEL_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.runs.cancel(thread_id, run_id, **cancel_payload)

    async def cancel_many(self, payload: dict[str, Any] | None = None) -> Any:
        cancel_many_payload = {
            key: payload[key]
            for key in self._BULK_CANCEL_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.runs.cancel_many(**cancel_many_payload)

    async def list(self, thread_id: str, payload: dict[str, Any] | None = None) -> Any:
        list_payload = {
            key: payload[key]
            for key in self._LIST_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.runs.list(thread_id, **list_payload)

    async def delete(self, thread_id: str, run_id: str) -> Any:
        return await self._client.runs.delete(thread_id, run_id)

    async def join(self, thread_id: str, run_id: str) -> Any:
        return await self._client.runs.join(thread_id, run_id)

    async def join_stream(
        self, thread_id: str, run_id: str, payload: dict[str, Any] | None = None
    ) -> Any:
        join_stream_payload = {
            key: payload[key]
            for key in self._JOIN_STREAM_FIELDS
            if payload is not None and key in payload
        }
        return self._client.runs.join_stream(thread_id, run_id, **join_stream_payload)

    async def create_cron(self, payload: dict[str, Any]) -> Any:
        assistant_id = payload["assistant_id"]
        cron_payload = {
            key: payload[key] for key in self._CRON_CREATE_FIELDS if key in payload
        }
        return await self._client.crons.create(assistant_id, **cron_payload)

    async def search_crons(self, payload: dict[str, Any] | None = None) -> Any:
        search_payload = {
            key: payload[key]
            for key in self._CRON_SEARCH_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.crons.search(**search_payload)

    async def count_crons(self, payload: dict[str, Any] | None = None) -> Any:
        count_payload = {
            key: payload[key]
            for key in self._CRON_COUNT_FIELDS
            if payload is not None and key in payload
        }
        return await self._client.crons.count(**count_payload)

    async def update_cron(self, cron_id: str, payload: dict[str, Any]) -> Any:
        update_payload = {
            key: payload[key] for key in self._CRON_UPDATE_FIELDS if key in payload
        }
        return await self._client.crons.update(cron_id, **update_payload)

    async def delete_cron(self, cron_id: str) -> Any:
        return await self._client.crons.delete(cron_id)

    async def create_cron_for_thread(
        self, thread_id: str, payload: dict[str, Any]
    ) -> Any:
        assistant_id = payload["assistant_id"]
        cron_payload = {
            key: payload[key] for key in self._CRON_CREATE_FIELDS if key in payload
        }
        return await self._client.crons.create_for_thread(
            thread_id, assistant_id, **cron_payload
        )
