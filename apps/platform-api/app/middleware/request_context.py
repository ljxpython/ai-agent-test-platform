from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request

logger = logging.getLogger("proxy")


def _request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id")
    if incoming:
        return incoming
    return uuid.uuid4().hex


def register_request_context_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        started = time.perf_counter()
        request_id = _request_id(request)
        request.state.request_id = request_id
        request.state.request_started_at = started
        logger.info(
            "request_started request_id=%s method=%s path=%s query=%s",
            request_id,
            request.method,
            request.url.path,
            request.url.query,
        )

        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "request_failed request_id=%s method=%s path=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                elapsed_ms,
            )
            raise

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["x-request-id"] = request_id
        logger.info(
            "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
