from __future__ import annotations

from typing import Any

import langgraph_sdk
from fastapi import Request

FORWARDED_HEADER_KEYS = ("authorization", "x-tenant-id", "x-project-id", "x-request-id")


def _forward_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    for key in FORWARDED_HEADER_KEYS:
        value = request.headers.get(key)
        if value:
            headers[key] = value

    if "x-request-id" not in headers:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            headers["x-request-id"] = str(request_id)

    return headers


def get_langgraph_client(request: Request) -> Any:
    settings = request.app.state.settings
    api_key = (
        settings.langgraph_upstream_api_key
        if settings.langgraph_upstream_api_key
        else None
    )
    return langgraph_sdk.get_client(
        url=settings.langgraph_upstream_url,
        api_key=api_key,
        headers=_forward_headers(request),
    )
