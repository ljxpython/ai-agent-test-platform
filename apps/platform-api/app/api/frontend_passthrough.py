from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

# Retired: routes in this module are no longer mounted in app/factory.py.
router = APIRouter(prefix="/api", tags=["frontend-passthrough"])


def _upstream_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _forward_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {
        "accept": request.headers.get("accept", "application/json"),
        "content-type": request.headers.get("content-type", "application/json"),
    }

    for key in ("authorization", "x-tenant-id", "x-project-id"):
        value = request.headers.get(key)
        if value:
            headers[key] = value

    if getattr(request.state, "request_id", None):
        headers["x-request-id"] = request.state.request_id

    settings = request.app.state.settings
    if settings.langgraph_upstream_api_key:
        headers["x-api-key"] = settings.langgraph_upstream_api_key

    return headers


async def _request_json(
    request: Request,
    method: str,
    path: str,
    *,
    payload: dict[str, Any] | None = None,
) -> Any:
    client: httpx.AsyncClient = request.app.state.client
    url = _upstream_url(request.app.state.settings.langgraph_upstream_url, path)
    response = await client.request(
        method=method, url=url, headers=_forward_headers(request), json=payload
    )

    if response.status_code >= 400:
        detail: Any
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    if not response.content:
        return {}

    try:
        return response.json()
    except Exception:
        return {"raw": response.text}


def _normalize_assistant_item(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    assistant_id = raw.get("assistant_id")
    if not isinstance(assistant_id, str) or not assistant_id:
        return None

    return {
        "assistant_id": assistant_id,
        "graph_id": (
            raw.get("graph_id") if isinstance(raw.get("graph_id"), str) else None
        ),
        "name": raw.get("name") if isinstance(raw.get("name"), str) else None,
    }


def _extract_messages(state: Any) -> list[dict[str, Any]]:
    if not isinstance(state, dict):
        return []
    values = state.get("values")
    if not isinstance(values, dict):
        return []
    messages = values.get("messages")
    if not isinstance(messages, list):
        return []

    items: list[dict[str, Any]] = []
    for raw in messages:
        if not isinstance(raw, dict):
            continue
        msg_type = str(raw.get("type") or raw.get("role") or "")
        role_map = {
            "human": "user",
            "user": "user",
            "ai": "ai",
            "assistant": "ai",
            "tool": "tool",
            "system": "system",
        }
        role = role_map.get(msg_type, msg_type or "unknown")

        items.append(
            {
                "id": str(raw.get("id")) if raw.get("id") is not None else None,
                "role": role,
                "type": msg_type,
                "content": raw.get("content"),
                "text": (
                    str(raw.get("content", ""))
                    if isinstance(raw.get("content"), str)
                    else ""
                ),
                "tool_call_id": (
                    str(raw.get("tool_call_id"))
                    if raw.get("tool_call_id") is not None
                    else None
                ),
                "name": str(raw.get("name")) if raw.get("name") is not None else None,
                "tool_calls": (
                    raw.get("tool_calls")
                    if isinstance(raw.get("tool_calls"), list)
                    else None
                ),
            }
        )
    return items


def _parse_json(raw: str | None, field_name: str) -> dict[str, Any] | None:
    if raw is None:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400, detail=f"{field_name} is invalid JSON"
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400, detail=f"{field_name} must be a JSON object"
        )
    return payload


async def _create_thread(
    request: Request, metadata: dict[str, Any] | None = None
) -> str:
    payload: dict[str, Any] = {}
    if metadata:
        payload["metadata"] = metadata
    created = await _request_json(request, "POST", "/threads", payload=payload)
    thread_id = created.get("thread_id") if isinstance(created, dict) else None
    if not isinstance(thread_id, str) or not thread_id:
        raise HTTPException(status_code=502, detail="Invalid thread create response")
    return thread_id


@router.post("/thread/new")
async def create_thread(
    request: Request, payload: dict[str, Any] | None = None
) -> dict[str, Any]:
    metadata = payload.get("metadata") if isinstance(payload, dict) else None
    if metadata is not None and not isinstance(metadata, dict):
        raise HTTPException(status_code=400, detail="metadata must be an object")
    thread_id = await _create_thread(request, metadata)
    user_id = payload.get("user_id") if isinstance(payload, dict) else None
    return {"thread_id": thread_id, "created": True, "user_id": user_id}


@router.post("/thread")
async def create_or_get_thread(
    request: Request, payload: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")
    user_id = payload.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    thread_id = await _create_thread(request)
    return {"user_id": user_id, "thread_id": thread_id, "created": True}


@router.get("/threads")
async def get_threads(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    rows = await _request_json(
        request,
        "POST",
        "/threads/search",
        payload={"limit": limit, "offset": offset},
    )
    if not isinstance(rows, list):
        rows = []

    items: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        thread_id = raw.get("thread_id")
        if not isinstance(thread_id, str) or not thread_id:
            continue
        items.append(
            {
                "thread_id": thread_id,
                "created_at": raw.get("created_at"),
                "updated_at": raw.get("updated_at"),
                "metadata": (
                    raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
                ),
                "status": raw.get("status"),
            }
        )
    return {"items": items}


@router.get("/state")
async def get_state(request: Request, thread_id: str | None = None) -> dict[str, Any]:
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    state = await _request_json(request, "GET", f"/threads/{thread_id}/state")
    return {"thread_id": thread_id, "state": state}


@router.get("/messages")
async def get_messages(
    request: Request,
    thread_id: str | None = None,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    state = await _request_json(request, "GET", f"/threads/{thread_id}/state")
    items = _extract_messages(state)
    end = max(0, len(items) - offset)
    start = max(0, end - limit)
    return {"thread_id": thread_id, "items": items[start:end]}


@router.get("/history")
async def get_history(
    request: Request,
    thread_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=200),
) -> dict[str, Any]:
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    history = await _request_json(
        request, "POST", f"/threads/{thread_id}/history", payload={"limit": limit}
    )
    if not isinstance(history, list):
        history = []
    return {"thread_id": thread_id, "items": history}


@router.get("/assistants")
async def get_assistants(
    request: Request,
    graph_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    payload: dict[str, Any] = {"limit": limit, "offset": offset}
    if graph_id:
        payload["graph_id"] = graph_id
    rows = await _request_json(request, "POST", "/assistants/search", payload=payload)
    if not isinstance(rows, list):
        rows = []
    items = [
        item
        for item in (_normalize_assistant_item(raw) for raw in rows)
        if item is not None
    ]
    return {"items": items}


@router.get("/graphs")
async def get_graphs(request: Request) -> dict[str, list[str]]:
    rows = await _request_json(
        request, "POST", "/assistants/search", payload={"limit": 500, "offset": 0}
    )
    graph_ids: set[str] = set()
    if isinstance(rows, list):
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            graph_id = raw.get("graph_id")
            if isinstance(graph_id, str) and graph_id:
                graph_ids.add(graph_id)
    return {"items": sorted(graph_ids)}


@router.get("/assistants/{assistant_id}")
async def get_assistant(request: Request, assistant_id: str) -> dict[str, Any]:
    item = await _request_json(request, "GET", f"/assistants/{assistant_id}")
    normalized = _normalize_assistant_item(item)
    if normalized is None:
        raise HTTPException(status_code=404, detail="assistant not found")
    return {"item": normalized}


@router.post("/assistants")
async def create_assistant(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")
    graph_id = payload.get("graph_id")
    if not isinstance(graph_id, str) or not graph_id:
        raise HTTPException(status_code=400, detail="graph_id is required")

    upstream_payload: dict[str, Any] = {"graph_id": graph_id}
    for key in (
        "name",
        "description",
        "config",
        "context",
        "metadata",
        "assistant_id",
        "if_exists",
    ):
        if key in payload:
            upstream_payload[key] = payload[key]

    item = await _request_json(request, "POST", "/assistants", payload=upstream_payload)
    normalized = _normalize_assistant_item(item)
    if normalized is None:
        raise HTTPException(status_code=502, detail="invalid assistant response")
    return {"item": normalized}


@router.patch("/assistants/{assistant_id}")
async def update_assistant(
    request: Request, assistant_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")
    upstream_payload: dict[str, Any] = {}
    for key in ("graph_id", "name", "description", "config", "context", "metadata"):
        if key in payload:
            upstream_payload[key] = payload[key]
    item = await _request_json(
        request, "PATCH", f"/assistants/{assistant_id}", payload=upstream_payload
    )
    normalized = _normalize_assistant_item(item)
    if normalized is None:
        raise HTTPException(status_code=502, detail="invalid assistant response")
    return {"item": normalized}


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(
    request: Request, assistant_id: str, delete_threads: bool = Query(default=False)
) -> dict[str, Any]:
    path = f"/assistants/{assistant_id}"
    if delete_threads:
        path = f"{path}?delete_threads=true"
    await _request_json(request, "DELETE", path)
    return {
        "assistant_id": assistant_id,
        "deleted": True,
        "delete_threads": delete_threads,
    }


@router.post("/chat/resume")
async def resume_chat(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")
    thread_id = payload.get("thread_id")
    if not isinstance(thread_id, str) or not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    assistant_id = payload.get("assistant_id")
    if not isinstance(assistant_id, str) or not assistant_id:
        raise HTTPException(status_code=400, detail="assistant_id is required")
    command = payload.get("command")
    if not isinstance(command, dict):
        raise HTTPException(status_code=400, detail="command must be object")

    run_payload: dict[str, Any] = {
        "assistant_id": assistant_id,
        "input": None,
        "command": command,
    }
    result = await _request_json(
        request,
        "POST",
        f"/threads/{thread_id}/runs/wait",
        payload=run_payload,
    )
    return {"thread_id": thread_id, "result": result}


@router.post("/chat/wait")
async def wait_chat(request: Request, payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload must be object")
    message = payload.get("message")
    if not isinstance(message, str) or not message:
        raise HTTPException(status_code=400, detail="message is required")
    assistant_id = payload.get("assistant_id")
    if not isinstance(assistant_id, str) or not assistant_id:
        raise HTTPException(status_code=400, detail="assistant_id is required")

    thread_id = payload.get("thread_id")
    resolved_thread_id = (
        thread_id
        if isinstance(thread_id, str) and thread_id
        else await _create_thread(request)
    )

    context = payload.get("context")
    if context is not None and not isinstance(context, dict):
        raise HTTPException(status_code=400, detail="context must be object")
    config = payload.get("config")
    if config is not None and not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="config must be object")

    run_payload: dict[str, Any] = {
        "assistant_id": assistant_id,
        "input": {"messages": [{"role": "human", "content": message}]},
    }
    if isinstance(context, dict):
        run_payload["context"] = context
    if isinstance(config, dict):
        run_payload["config"] = config

    result = await _request_json(
        request, "POST", f"/threads/{resolved_thread_id}/runs/wait", payload=run_payload
    )
    return {"thread_id": resolved_thread_id, "result": result}


@router.get("/chat/stream")
async def chat_stream(
    request: Request,
    message: str,
    assistant_id: str,
    thread_id: str | None = None,
    stream_mode: str | None = None,
    context_json: str | None = Query(default=None),
    config_json: str | None = Query(default=None),
) -> StreamingResponse:
    resolved_thread_id = thread_id or await _create_thread(request)
    modes = [
        item.strip()
        for item in (stream_mode or "messages,updates,tasks,checkpoints,debug").split(
            ","
        )
        if item.strip()
    ]
    context = _parse_json(context_json, "context_json")
    config = _parse_json(config_json, "config_json")

    payload: dict[str, Any] = {
        "assistant_id": assistant_id,
        "input": {"messages": [{"role": "human", "content": message}]},
        "stream_mode": modes,
    }
    if context is not None:
        payload["context"] = context
    if config is not None:
        payload["config"] = config

    client: httpx.AsyncClient = request.app.state.client
    url = _upstream_url(
        request.app.state.settings.langgraph_upstream_url,
        f"/threads/{resolved_thread_id}/runs/stream",
    )
    upstream = await client.send(
        client.build_request(
            "POST", url, headers=_forward_headers(request), json=payload
        ),
        stream=True,
    )

    if upstream.status_code >= 400:
        body = await upstream.aread()
        await upstream.aclose()
        try:
            detail = (
                json.loads(body.decode("utf-8"))
                if body
                else {"error": "upstream_error"}
            )
        except Exception:
            detail = {"error": body.decode("utf-8", errors="ignore")}
        raise HTTPException(status_code=upstream.status_code, detail=detail)

    async def stream_body():
        try:
            async for chunk in upstream.aiter_raw():
                if chunk:
                    yield chunk
        finally:
            await upstream.aclose()

    return StreamingResponse(
        stream_body(),
        media_type=upstream.headers.get("content-type", "text/event-stream"),
        headers={"x-thread-id": resolved_thread_id},
    )


@router.get("/run-logs")
async def run_logs() -> JSONResponse:
    return JSONResponse(content={"items": []})


@router.api_route(
    "/langgraph/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def langgraph_prefixed_passthrough(request: Request, full_path: str) -> Response:
    return await langgraph_raw_passthrough(request, full_path)


@router.api_route(
    "/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def langgraph_raw_passthrough(request: Request, full_path: str) -> Response:
    client: httpx.AsyncClient = request.app.state.client
    target = _upstream_url(
        request.app.state.settings.langgraph_upstream_url, f"/{full_path}"
    )
    if request.url.query:
        target = f"{target}?{request.url.query}"

    body = await request.body()
    headers = _forward_headers(request)
    if not body:
        headers.pop("content-type", None)

    upstream = await client.send(
        client.build_request(request.method, target, headers=headers, content=body),
        stream=True,
    )

    content_type = upstream.headers.get("content-type", "")
    if content_type.startswith("text/event-stream"):

        async def stream_body():
            try:
                async for chunk in upstream.aiter_raw():
                    if chunk:
                        yield chunk
            finally:
                await upstream.aclose()

        return StreamingResponse(
            stream_body(),
            status_code=upstream.status_code,
            media_type=content_type,
        )

    payload = await upstream.aread()
    response_headers: dict[str, str] = {}
    if content_type:
        response_headers["content-type"] = content_type
    await upstream.aclose()
    return Response(
        content=payload, status_code=upstream.status_code, headers=response_headers
    )
