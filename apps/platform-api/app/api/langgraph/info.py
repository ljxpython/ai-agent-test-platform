from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request

router = APIRouter()


def _forward_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {"accept": "application/json"}
    for key in ("authorization", "x-tenant-id", "x-project-id", "x-request-id"):
        value = request.headers.get(key)
        if value:
            headers[key] = value

    settings = request.app.state.settings
    if settings.langgraph_upstream_api_key:
        headers["x-api-key"] = settings.langgraph_upstream_api_key

    if "x-request-id" not in headers:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            headers["x-request-id"] = str(request_id)

    return headers


@router.get("/info")
async def get_runtime_info(request: Request) -> Any:
    client: httpx.AsyncClient = request.app.state.client
    base_url: str = request.app.state.settings.langgraph_upstream_url
    url = f"{base_url.rstrip('/')}/info"

    try:
        response = await client.get(url, headers=_forward_headers(request))
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail=f"langgraph_info_timeout: {exc}"
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail=f"langgraph_info_unavailable: {exc}"
        ) from exc

    if response.status_code >= 400:
        try:
            detail: Any = response.json()
        except Exception:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    try:
        return response.json()
    except Exception:
        return {"raw": response.text}
