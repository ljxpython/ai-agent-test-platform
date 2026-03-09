from __future__ import annotations

import uuid
from datetime import timezone

from app.db.access import (
    create_user_account,
    get_user_by_id,
    get_user_by_username,
    list_user_project_memberships,
    list_users,
    parse_uuid,
    update_user_password_hash,
)
from app.db.session import session_scope
from app.security.password import hash_password
from fastapi import APIRouter, HTTPException, Query, Request

from .common import (
    current_user_id_from_request,
    require_db_session_factory,
    user_has_admin_capability,
)
from .schemas import CreateUserRequest, UpdateMeRequest, UpdateUserRequest

router = APIRouter(prefix="/users", tags=["management-users"])


def _to_iso8601(dt):
    if dt is None:
        return None
    if getattr(dt, "tzinfo", None) is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _serialize_user(row):
    return {
        "id": str(row.id),
        "username": row.username,
        "status": row.status,
        "is_super_admin": bool(row.is_super_admin),
        "email": row.email,
        "created_at": _to_iso8601(row.created_at),
        "updated_at": _to_iso8601(row.updated_at),
    }


@router.get("")
async def get_users(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    query: str | None = Query(None),
    status: str | None = Query(None),
    exclude_user_ids: str | None = Query(None),
):
    user_id = current_user_id_from_request(request)
    if not user_has_admin_capability(request, user_id):
        raise HTTPException(status_code=403, detail="admin_required")

    session_factory = require_db_session_factory(request)
    excluded_ids: list[uuid.UUID] = []
    if isinstance(exclude_user_ids, str) and exclude_user_ids.strip():
        for raw in exclude_user_ids.split(","):
            normalized = raw.strip()
            if not normalized:
                continue
            parsed = parse_uuid(normalized)
            if parsed is not None:
                excluded_ids.append(parsed)

    with session_scope(session_factory) as session:
        rows, total = list_users(
            session,
            limit=limit,
            offset=offset,
            query=query,
            status=status,
            exclude_user_ids=excluded_ids,
        )
        return {
            "items": [_serialize_user(row) for row in rows],
            "total": total,
        }


@router.post("")
async def create_user(request: Request, payload: CreateUserRequest):
    user_id = current_user_id_from_request(request)
    if not user_has_admin_capability(request, user_id):
        raise HTTPException(status_code=403, detail="admin_required")

    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        existing = get_user_by_username(session, payload.username)
        if existing is not None:
            raise HTTPException(status_code=409, detail="username_already_exists")
        row = create_user_account(
            session,
            username=payload.username,
            password_hash=hash_password(payload.password),
            is_super_admin=payload.is_super_admin,
        )
        return _serialize_user(row)


@router.get("/me")
async def get_me(request: Request):
    user_id = current_user_id_from_request(request)
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        row = get_user_by_id(session, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="user_not_found")
        return _serialize_user(row)


@router.patch("/me")
async def update_me(request: Request, payload: UpdateMeRequest):
    user_id = current_user_id_from_request(request)
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        row = get_user_by_id(session, user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="user_not_found")

        if payload.username is not None:
            normalized_username = payload.username.strip()
            existing = get_user_by_username(session, normalized_username)
            if existing is not None and existing.id != row.id:
                raise HTTPException(status_code=409, detail="username_already_exists")
            row.username = normalized_username
            row.external_subject = normalized_username

        if payload.email is not None:
            normalized_email = payload.email.strip()
            row.email = normalized_email or None

        session.flush()
        return _serialize_user(row)


@router.get("/{user_id}")
async def get_user_detail(request: Request, user_id: str):
    actor_user_id = current_user_id_from_request(request)
    if not user_has_admin_capability(request, actor_user_id):
        raise HTTPException(status_code=403, detail="admin_required")

    target_user_id = parse_uuid(user_id)
    if target_user_id is None:
        raise HTTPException(status_code=400, detail="invalid_user_id")

    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        row = get_user_by_id(session, target_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="user_not_found")
        return _serialize_user(row)


@router.get("/{user_id}/projects")
async def get_user_projects(request: Request, user_id: str):
    actor_user_id = current_user_id_from_request(request)
    if not user_has_admin_capability(request, actor_user_id):
        raise HTTPException(status_code=403, detail="admin_required")

    target_user_id = parse_uuid(user_id)
    if target_user_id is None:
        raise HTTPException(status_code=400, detail="invalid_user_id")

    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        row = get_user_by_id(session, target_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="user_not_found")

        links = list_user_project_memberships(session, target_user_id)
        return {
            "items": [
                {
                    "project_id": str(project.id),
                    "project_name": project.name,
                    "project_description": project.description,
                    "project_status": project.status,
                    "role": member.role,
                    "joined_at": _to_iso8601(member.created_at),
                }
                for member, project in links
            ],
            "total": len(links),
        }


@router.patch("/{user_id}")
async def update_user(request: Request, user_id: str, payload: UpdateUserRequest):
    actor_user_id = current_user_id_from_request(request)
    if not user_has_admin_capability(request, actor_user_id):
        raise HTTPException(status_code=403, detail="admin_required")

    target_user_id = parse_uuid(user_id)
    if target_user_id is None:
        raise HTTPException(status_code=400, detail="invalid_user_id")

    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        row = get_user_by_id(session, target_user_id)
        if row is None:
            raise HTTPException(status_code=404, detail="user_not_found")

        if payload.username is not None:
            normalized_username = payload.username.strip()
            existing = get_user_by_username(session, normalized_username)
            if existing is not None and existing.id != row.id:
                raise HTTPException(status_code=409, detail="username_already_exists")
            row.username = normalized_username
            row.external_subject = normalized_username

        if payload.status is not None:
            row.status = payload.status

        if payload.is_super_admin is not None:
            row.is_super_admin = bool(payload.is_super_admin)

        if payload.password is not None:
            update_user_password_hash(session, row, hash_password(payload.password))

        session.flush()
        return _serialize_user(row)
