from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from langgraph_sdk import get_client

if os.getenv("RUN_REAL_LANGGRAPH_TESTS") != "1":
    pytest.skip(
        "Set RUN_REAL_LANGGRAPH_TESTS=1 to run real LangGraph upstream integration tests.",
        allow_module_level=True,
    )


def _to_dict(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    if hasattr(value, "dict") and callable(value.dict):
        return value.dict()
    if hasattr(value, "__dict__"):
        return {k: v for k, v in vars(value).items() if not k.startswith("_")}
    return value


def _extract_id(value: Any, *keys: str) -> str:
    data = _to_dict(value)
    if isinstance(data, dict):
        for key in keys:
            candidate = data.get(key)
            if candidate:
                return str(candidate)
    return ""


def _content_has_text(content: Any) -> bool:
    if isinstance(content, str):
        return bool(content.strip())
    if isinstance(content, list):
        return any(_content_has_text(item) for item in content)
    if isinstance(content, dict):
        if _content_has_text(content.get("text")):
            return True
        if _content_has_text(content.get("content")):
            return True
        return any(_content_has_text(item) for item in content.values())
    return False


def _collect_message_dicts(payload: Any) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    stack: list[Any] = [_to_dict(payload)]

    while stack:
        current = stack.pop()
        if isinstance(current, list):
            stack.extend(_to_dict(item) for item in current)
            continue
        if not isinstance(current, dict):
            normalized = _to_dict(current)
            if isinstance(normalized, dict):
                stack.append(normalized)
            continue

        role = current.get("role") or current.get("type")
        if role is not None and ("content" in current or "data" in current):
            messages.append(current)

        nested_messages = current.get("messages")
        if isinstance(nested_messages, list):
            for item in nested_messages:
                normalized_item = _to_dict(item)
                if isinstance(normalized_item, dict):
                    messages.append(normalized_item)

        stack.extend(_to_dict(item) for item in current.values())

    return messages


def _is_assistant_output_message(message: dict[str, Any]) -> bool:
    role = str(message.get("role") or message.get("type") or "").lower()
    if role not in {"assistant", "ai"}:
        return False
    if _content_has_text(message.get("content")):
        return True
    data = message.get("data")
    if isinstance(data, dict) and _content_has_text(data.get("content")):
        return True
    return False


@pytest.mark.asyncio
async def test_real_langgraph_sdk_create_run_and_collect_output() -> None:
    # Given a real upstream and a unique integration marker.
    upstream_url = os.getenv("LANGGRAPH_UPSTREAM_URL", "http://127.0.0.1:8123")
    graph_id = os.getenv("LANGGRAPH_TEST_GRAPH_ID", "assistant")
    marker = f"it-{uuid.uuid4().hex}"
    assistant_id = str(uuid.uuid4())
    thread_id = ""

    client = get_client(url=upstream_url)

    try:
        # When creating assistant/thread and waiting for a user run.
        created_assistant = await client.assistants.create(
            assistant_id=assistant_id,
            graph_id=graph_id,
            metadata={"it_marker": marker},
            name=f"Integration {marker}",
            description="Real SDK integration test",
        )
        assistant_id = (
            _extract_id(created_assistant, "assistant_id", "id") or assistant_id
        )

        created_thread = await client.threads.create(metadata={"it_marker": marker})
        thread_id = _extract_id(created_thread, "thread_id", "id")
        assert thread_id, f"Expected thread id in response, got: {created_thread!r}"

        run_result = await client.runs.wait(
            thread_id,
            assistant_id,
            input={
                "messages": [
                    {
                        "role": "user",
                        "content": f"Reply briefly with a greeting. marker={marker}",
                    }
                ]
            },
        )

        state = await client.threads.get_state(thread_id)
        history = await client.threads.get_history(thread_id)

        # Then run/state/history should contain assistant or ai output content.
        message_candidates = _collect_message_dicts([run_result, state, history])
        assert any(_is_assistant_output_message(msg) for msg in message_candidates), (
            "Expected at least one assistant/ai message with non-empty content "
            "in run/state/history payloads"
        )
    finally:
        if thread_id:
            try:
                await client.threads.delete(thread_id)
            except Exception:
                pass
        if assistant_id:
            try:
                await client.assistants.delete(assistant_id, delete_threads=True)
            except Exception:
                pass
        close = getattr(client, "aclose", None)
        if callable(close):
            await close()
