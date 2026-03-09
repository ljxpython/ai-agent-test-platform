from __future__ import annotations

import logging
import time

from app.config import Settings
from app.db.access import create_audit_log, parse_uuid
from app.db.session import session_scope
from fastapi import FastAPI, Request

logger = logging.getLogger("proxy")


def _audit_plane(path: str) -> str:
    if path.startswith("/_platform/"):
        return "control_plane"
    if path.startswith("/_proxy/"):
        return "internal"
    return "runtime_proxy"


def _management_action(path: str, method: str) -> tuple[str, str | None, str | None]:
    normalized_path = path.strip("/")
    segments = normalized_path.split("/") if normalized_path else []
    if len(segments) < 2 or segments[0] != "_management":
        return "http.request", None, None

    if segments[:3] == ["_management", "auth", "login"] and method == "POST":
        return "auth.login", "user", None
    if segments[:3] == ["_management", "auth", "refresh"] and method == "POST":
        return "auth.refresh", "user", None
    if segments[:3] == ["_management", "auth", "logout"] and method == "POST":
        return "auth.logout", "user", None
    if segments[:3] == ["_management", "auth", "change-password"] and method == "POST":
        return "user.password_changed", "user", None

    if len(segments) >= 2 and segments[1] == "users":
        if method == "POST":
            return "user.created", "user", None
        if method == "GET":
            return "user.listed", "user", None

    if len(segments) >= 2 and segments[1] == "projects":
        if len(segments) == 2 and method == "GET":
            return "project.listed", "project", None
        if len(segments) == 2 and method == "POST":
            return "project.created", "project", None
        if len(segments) == 3 and method == "DELETE":
            return "project.deleted", "project", segments[2]
        if len(segments) >= 4 and segments[3] == "members":
            project_id = segments[2]
            if len(segments) == 4 and method == "GET":
                return "member.listed", "project_member", project_id
            if len(segments) == 4 and method == "POST":
                return "member.upserted", "project_member", project_id
            if len(segments) == 5 and method == "DELETE":
                return "member.removed", "project_member", project_id

    if len(segments) >= 2 and segments[1] == "audit" and method == "GET":
        return "audit.listed", "audit_log", None

    return "http.request", None, None


def _to_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _duration_ms(request: Request, fallback_started_at: float) -> float:
    started_at = getattr(request.state, "request_started_at", fallback_started_at)
    return round((time.perf_counter() - started_at) * 1000, 2)


def register_audit_log_middleware(app: FastAPI, settings: Settings) -> None:
    @app.middleware("http")
    async def audit_log_middleware(request: Request, call_next):
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = _duration_ms(request, started)
            action, target_type, target_id = _management_action(
                request.url.path, request.method
            )
            if settings.platform_db_enabled:
                session_factory = getattr(request.app.state, "db_session_factory", None)
                if session_factory is not None:
                    try:
                        with session_scope(session_factory) as session:
                            create_audit_log(
                                session=session,
                                request_id=getattr(request.state, "request_id", "-"),
                                plane=_audit_plane(request.url.path),
                                method=request.method,
                                path=request.url.path,
                                query=request.url.query,
                                status_code=500,
                                duration_ms=int(elapsed_ms),
                                project_id=parse_uuid(
                                    getattr(request.state, "project_id", "")
                                    or request.headers.get("x-project-id", "")
                                ),
                                tenant_id=parse_uuid(
                                    getattr(request.state, "tenant_id", "") or ""
                                ),
                                user_id=parse_uuid(
                                    getattr(request.state, "user_id", "") or ""
                                ),
                                user_subject=getattr(
                                    request.state, "user_subject", None
                                ),
                                client_ip=(
                                    request.client.host if request.client else None
                                ),
                                user_agent=request.headers.get("user-agent"),
                                response_size=None,
                                metadata_json={
                                    "action": action,
                                    "target_type": target_type,
                                    "target_id": target_id,
                                    "result": "failed",
                                    "route_kind": _audit_plane(request.url.path),
                                    "error": True,
                                },
                            )
                    except Exception:
                        logger.exception(
                            "audit_write_failed request_id=%s",
                            getattr(request.state, "request_id", "-"),
                        )
            raise

        elapsed_ms = _duration_ms(request, started)
        action, target_type, target_id = _management_action(
            request.url.path, request.method
        )
        if settings.platform_db_enabled:
            session_factory = getattr(request.app.state, "db_session_factory", None)
            if session_factory is not None:
                try:
                    with session_scope(session_factory) as session:
                        create_audit_log(
                            session=session,
                            request_id=getattr(request.state, "request_id", "-"),
                            plane=_audit_plane(request.url.path),
                            method=request.method,
                            path=request.url.path,
                            query=request.url.query,
                            status_code=response.status_code,
                            duration_ms=int(elapsed_ms),
                            project_id=parse_uuid(
                                getattr(request.state, "project_id", "")
                                or request.headers.get("x-project-id", "")
                            ),
                            tenant_id=parse_uuid(
                                getattr(request.state, "tenant_id", "") or ""
                            ),
                            user_id=parse_uuid(
                                getattr(request.state, "user_id", "") or ""
                            ),
                            user_subject=getattr(request.state, "user_subject", None),
                            client_ip=request.client.host if request.client else None,
                            user_agent=request.headers.get("user-agent"),
                            response_size=_to_int(
                                response.headers.get("content-length")
                            ),
                            metadata_json={
                                "action": action,
                                "target_type": target_type,
                                "target_id": target_id,
                                "result": (
                                    "success"
                                    if response.status_code < 400
                                    else "failed"
                                ),
                                "route_kind": _audit_plane(request.url.path),
                                "has_tenant_header": bool(
                                    request.headers.get("x-tenant-id")
                                ),
                            },
                        )
                except Exception:
                    logger.exception(
                        "audit_write_failed request_id=%s",
                        getattr(request.state, "request_id", "-"),
                    )
        return response
