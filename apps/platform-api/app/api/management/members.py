from __future__ import annotations

from app.db.access import (
    count_project_admins,
    get_project_member,
    get_user_by_id,
    list_project_members,
    parse_uuid,
    remove_project_member,
    upsert_project_member,
)
from app.db.session import session_scope
from fastapi import APIRouter, HTTPException, Query, Request

from .common import require_db_session_factory, require_project_role
from .schemas import UpsertMemberRequest

router = APIRouter(prefix="/projects/{project_id}/members", tags=["management-members"])


@router.get("")
async def get_members(
    request: Request, project_id: str, query: str | None = Query(None)
):
    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor", "executor"}
    )
    session_factory = require_db_session_factory(request)

    with session_scope(session_factory) as session:
        rows = list_project_members(session, project_uuid)
        normalized_query = (
            query.strip().lower() if isinstance(query, str) and query.strip() else None
        )
        result: list[dict[str, str]] = []
        for row in rows:
            user = get_user_by_id(session, row.user_id)
            username = user.username if user else "unknown"
            if (
                normalized_query is not None
                and normalized_query not in username.lower()
            ):
                continue
            result.append(
                {
                    "user_id": str(row.user_id),
                    "username": username,
                    "role": row.role,
                }
            )
        return {"items": result}


@router.post("")
async def upsert_member(
    request: Request, project_id: str, payload: UpsertMemberRequest
):
    project_uuid = parse_uuid(project_id)
    target_user_id = parse_uuid(payload.user_id)
    if project_uuid is None or target_user_id is None:
        raise HTTPException(status_code=400, detail="invalid_id")

    actor_user_id, actor_role = require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor"}
    )
    if payload.role not in {"admin", "editor", "executor"}:
        raise HTTPException(status_code=400, detail="invalid_role")
    if actor_role == "editor" and payload.role in {"admin", "editor"}:
        raise HTTPException(
            status_code=403, detail="editor_cannot_assign_admin_or_editor"
        )

    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        target = get_user_by_id(session, target_user_id)
        if target is None:
            raise HTTPException(status_code=404, detail="user_not_found")

        existing = get_project_member(session, project_uuid, target_user_id)
        if (
            existing is not None
            and existing.role == "admin"
            and payload.role != "admin"
        ):
            if count_project_admins(session, project_uuid) <= 1:
                raise HTTPException(
                    status_code=409, detail="cannot_downgrade_last_admin"
                )

        row = upsert_project_member(session, project_uuid, target_user_id, payload.role)
        return {
            "user_id": str(row.user_id),
            "username": target.username,
            "role": row.role,
            "updated_by": str(actor_user_id),
        }


@router.delete("/{user_id}")
async def delete_member(request: Request, project_id: str, user_id: str):
    project_uuid = parse_uuid(project_id)
    target_user_id = parse_uuid(user_id)
    if project_uuid is None or target_user_id is None:
        raise HTTPException(status_code=400, detail="invalid_id")

    _, actor_role = require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        member = get_project_member(session, project_uuid, target_user_id)
        if member is None:
            raise HTTPException(status_code=404, detail="member_not_found")
        if actor_role == "editor" and member.role != "executor":
            raise HTTPException(
                status_code=403, detail="editor_can_only_remove_executor"
            )
        if member.role == "admin" and count_project_admins(session, project_uuid) <= 1:
            raise HTTPException(status_code=409, detail="cannot_remove_last_admin")

        remove_project_member(session, member)
    return {"ok": True}
