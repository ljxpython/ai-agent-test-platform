from __future__ import annotations

from typing import AsyncIterator

import httpx
from app.config import Settings
from fastapi import Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

# Retired: passthrough entrypoints are no longer mounted in app/factory.py.
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def _strip_request_headers(headers: dict[str, str]) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in headers.items():
        lower_key = key.lower()
        if lower_key in HOP_BY_HOP_HEADERS or lower_key in {"host", "content-length"}:
            continue
        cleaned[key] = value
    return cleaned


def _strip_response_headers(headers: httpx.Headers) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in headers.items():
        lower_key = key.lower()
        if lower_key in HOP_BY_HOP_HEADERS or lower_key == "content-length":
            continue
        cleaned[key] = value
    return cleaned


def _upstream_url(base_url: str, path: str, query: str) -> str:
    normalized_base = base_url.rstrip("/")
    normalized_path = path.lstrip("/")
    url = f"{normalized_base}/{normalized_path}"
    if query:
        return f"{url}?{query}"
    return url


def _cors_json_error(request: Request, status_code: int, content: dict) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Vary": "Origin",
        },
    )


async def passthrough_request(
    request: Request,
    full_path: str,
    settings: Settings,
    logger,
) -> Response:
    upstream_base_url = settings.langgraph_upstream_url
    upstream_api_key = settings.langgraph_upstream_api_key
    upstream_url = _upstream_url(upstream_base_url, full_path, request.url.query)

    headers = _strip_request_headers(dict(request.headers))
    headers["x-request-id"] = getattr(request.state, "request_id", "-")
    if upstream_api_key:
        headers["x-api-key"] = upstream_api_key

    body = await request.body()
    retries = settings.proxy_upstream_retries
    attempt = 0
    upstream_response = None

    while attempt <= retries:
        try:
            upstream_request = request.app.state.client.build_request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                content=body,
            )
            upstream_response = await request.app.state.client.send(
                upstream_request, stream=True
            )
            break
        except httpx.TimeoutException as exc:
            if attempt < retries:
                attempt += 1
                continue
            return _cors_json_error(
                request,
                504,
                {
                    "error": "gateway_timeout",
                    "message": f"Upstream timeout: {exc}",
                    "request_id": getattr(request.state, "request_id", "-"),
                },
            )
        except httpx.HTTPError as exc:
            if attempt < retries:
                attempt += 1
                continue
            return _cors_json_error(
                request,
                502,
                {
                    "error": "bad_gateway",
                    "message": f"Failed to reach upstream: {exc}",
                    "request_id": getattr(request.state, "request_id", "-"),
                },
            )

    if upstream_response is None:
        return _cors_json_error(
            request,
            502,
            {
                "error": "bad_gateway",
                "message": "Failed to reach upstream",
                "request_id": getattr(request.state, "request_id", "-"),
            },
        )

    response_headers = _strip_response_headers(upstream_response.headers)
    logger.info(
        "passthrough_upstream_response request_id=%s status=%s content_type=%s",
        getattr(request.state, "request_id", "-"),
        upstream_response.status_code,
        upstream_response.headers.get("content-type"),
    )

    async def stream_body() -> AsyncIterator[bytes]:
        try:
            async for chunk in upstream_response.aiter_raw():
                if chunk:
                    yield chunk
        finally:
            await upstream_response.aclose()

    return StreamingResponse(
        stream_body(),
        status_code=upstream_response.status_code,
        headers=response_headers,
        media_type=upstream_response.headers.get("content-type"),
    )
