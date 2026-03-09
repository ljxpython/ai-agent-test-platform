from __future__ import annotations

from datetime import datetime, timezone

from app.db.access import (
    create_project,
    get_or_create_default_tenant,
    get_user_by_id,
    list_active_projects,
    list_active_projects_for_user,
    parse_uuid,
    upsert_project_member,
)
from app.db.models import Project
from app.db.session import session_scope
from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from .common import (
    current_user_id_from_request,
    require_db_session_factory,
    require_project_role,
)
from .schemas import CreateProjectRequest

router = APIRouter(prefix="/projects", tags=["management-projects"])


@router.get("")
async def list_projects(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    query: str | None = Query(None),
):
    actor_user_id = current_user_id_from_request(request)
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        actor = get_user_by_id(session, actor_user_id)
        if actor is not None and actor.is_super_admin:
            rows, total = list_active_projects(
                session, limit=limit, offset=offset, query=query
            )
        else:
            rows, total = list_active_projects_for_user(
                session,
                user_id=actor_user_id,
                limit=limit,
                offset=offset,
                query=query,
            )
        return {
            "items": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "status": row.status,
                }
                for row in rows
            ],
            "total": total,
        }


@router.post("")
async def create_new_project(request: Request, payload: CreateProjectRequest):
    user_id = current_user_id_from_request(request)
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        tenant = get_or_create_default_tenant(session)
        try:
            row = create_project(
                session,
                tenant_id=tenant.id,
                name=payload.name,
                description=payload.description,
            )
            session.flush()
        except IntegrityError as exc:
            raw_message = str(getattr(exc, "orig", exc)).lower()
            if (
                "projects.code" in raw_message
                or "uq" in raw_message
                and "code" in raw_message
            ):
                raise HTTPException(
                    status_code=409, detail="project_code_already_exists"
                ) from exc
            raise HTTPException(status_code=409, detail="project_conflict") from exc

        upsert_project_member(session, project_id=row.id, user_id=user_id, role="admin")
        return {
            "id": str(row.id),
            "name": row.name,
            "description": row.description,
            "status": row.status,
        }


@router.delete("/{project_id}")
async def delete_project(request: Request, project_id: str):
    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")

    require_project_role(request, project_uuid, allowed_roles={"admin"})
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        row = session.get(Project, project_uuid)
        if row is None:
            raise HTTPException(status_code=404, detail="project_not_found")
        row.status = "deleting"
        session.flush()
        row.status = "deleted"
        row.deleted_at = datetime.now(timezone.utc)
        session.flush()
    return {"ok": True}
