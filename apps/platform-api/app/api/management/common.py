from __future__ import annotations

import uuid

from app.db.access import get_project_member, get_user_by_id, parse_uuid
from app.db.models import ProjectMember
from app.db.session import session_scope
from fastapi import HTTPException, Request
from sqlalchemy import select


def current_user_id_from_request(request: Request) -> uuid.UUID:
    user_id = parse_uuid(str(getattr(request.state, "user_id", "") or ""))
    if user_id is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return user_id


def require_db_session_factory(request: Request):
    session_factory = getattr(request.app.state, "db_session_factory", None)
    if session_factory is None:
        raise HTTPException(status_code=503, detail="database_not_enabled")
    return session_factory


def user_has_admin_capability(request: Request, user_id: uuid.UUID) -> bool:
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        user = get_user_by_id(session, user_id)
        if user is not None and user.is_super_admin:
            return True
        stmt = (
            select(ProjectMember.id)
            .where(ProjectMember.user_id == user_id, ProjectMember.role == "admin")
            .limit(1)
        )
        return session.scalar(stmt) is not None


def role_in_project(
    request: Request, project_id: uuid.UUID, user_id: uuid.UUID
) -> str | None:
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        user = get_user_by_id(session, user_id)
        if user is not None and user.is_super_admin:
            return "admin"
        member = get_project_member(session, project_id=project_id, user_id=user_id)
        return member.role if member is not None else None


def require_project_role(
    request: Request, project_id: uuid.UUID, *, allowed_roles: set[str]
) -> tuple[uuid.UUID, str]:
    user_id = current_user_id_from_request(request)
    role = role_in_project(request, project_id=project_id, user_id=user_id)
    if role not in allowed_roles:
        raise HTTPException(status_code=403, detail="insufficient_project_role")
    request.state.project_id = str(project_id)
    return user_id, role or ""
