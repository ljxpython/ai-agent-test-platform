from __future__ import annotations

import uuid
from typing import Any

from app.db.access import get_agent_by_project_and_langgraph_assistant_id, parse_uuid
from app.db.session import session_scope
from app.services.langgraph_sdk.client import get_langgraph_client
from fastapi import HTTPException, Request

_PROJECT_ID_HEADER = "x-project-id"
_THREAD_PROJECT_ID_KEYS = ("project_id", "x-project-id", "projectId")


def _scope_guard_enabled(request: Request) -> bool:
    settings = getattr(request.app.state, "settings", None)
    return bool(getattr(settings, "langgraph_scope_guard_enabled", False))


def _require_db_session_factory(request: Request) -> Any:
    session_factory = getattr(request.app.state, "db_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="Database is not enabled")
    return session_factory


def _normalize_project_id(raw_project_id: Any) -> str | None:
    if isinstance(raw_project_id, uuid.UUID):
        return str(raw_project_id)
    if not isinstance(raw_project_id, str) or not raw_project_id:
        return None
    parsed = parse_uuid(raw_project_id)
    if parsed is None:
        return None
    return str(parsed)


def _thread_project_id_from_metadata(thread: Any) -> str | None:
    if isinstance(thread, dict):
        metadata = thread.get("metadata")
    else:
        metadata = getattr(thread, "metadata", None)

    if not isinstance(metadata, dict):
        return None

    for key in _THREAD_PROJECT_ID_KEYS:
        normalized = _normalize_project_id(metadata.get(key))
        if normalized is not None:
            return normalized
    return None


def require_project_id(request: Request) -> str:
    if not _scope_guard_enabled(request):
        return ""

    raw_project_id = request.headers.get(_PROJECT_ID_HEADER)
    normalized = _normalize_project_id(raw_project_id)
    if normalized is None:
        raise HTTPException(
            status_code=400,
            detail="x-project-id header is required and must be a valid UUID",
        )
    return normalized


async def assert_assistant_belongs_project(request: Request, assistant_id: str) -> None:
    if not _scope_guard_enabled(request):
        return

    project_uuid = uuid.UUID(require_project_id(request))
    session_factory = _require_db_session_factory(request)
    with session_scope(session_factory) as session:
        agent = get_agent_by_project_and_langgraph_assistant_id(
            session,
            project_id=project_uuid,
            langgraph_assistant_id=assistant_id,
        )
    if agent is None:
        raise HTTPException(status_code=403, detail="assistant_project_denied")


async def assert_thread_belongs_project(request: Request, thread_id: str) -> None:
    if not _scope_guard_enabled(request):
        return

    project_id = require_project_id(request)
    client = get_langgraph_client(request)
    try:
        thread = await client.threads.get(thread_id)
    except Exception as exc:
        # 上游 LangGraph 不可用时，统一转换为可控网关错误，避免直接抛 500。
        raise HTTPException(
            status_code=502, detail="langgraph_upstream_unavailable"
        ) from exc
    thread_project_id = _thread_project_id_from_metadata(thread)
    # 无 project 元数据也按越权处理，避免 thread 在项目边界外被探测。
    if thread_project_id is None or thread_project_id != project_id:
        raise HTTPException(status_code=403, detail="thread_project_denied")


def inject_project_metadata(
    request: Request, payload: dict[str, Any]
) -> dict[str, Any]:
    if not _scope_guard_enabled(request):
        return dict(payload) if isinstance(payload, dict) else {}

    project_id = require_project_id(request)
    next_payload = dict(payload) if isinstance(payload, dict) else {}
    metadata = next_payload.get("metadata")
    metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
    metadata_dict["project_id"] = project_id
    next_payload["metadata"] = metadata_dict
    return next_payload
