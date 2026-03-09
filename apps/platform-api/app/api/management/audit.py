from __future__ import annotations

from typing import Any

from app.db.access import list_audit_logs, list_audit_logs_for_project, parse_uuid
from app.db.session import session_scope
from fastapi import APIRouter, HTTPException, Query, Request

from .common import (
    current_user_id_from_request,
    require_db_session_factory,
    require_project_role,
    user_has_admin_capability,
)

router = APIRouter(prefix="/audit", tags=["management-audit"])


def _matches_metadata_filters(
    metadata_json: Any,
    *,
    action: str | None,
    target_type: str | None,
    target_id: str | None,
) -> bool:
    if not isinstance(metadata_json, dict):
        return action is None and target_type is None and target_id is None

    if action is not None and str(metadata_json.get("action") or "") != action:
        return False
    if (
        target_type is not None
        and str(metadata_json.get("target_type") or "") != target_type
    ):
        return False
    if target_id is not None and str(metadata_json.get("target_id") or "") != target_id:
        return False
    return True


def _serialize_audit_row(row):
    metadata_json = row.metadata_json if isinstance(row.metadata_json, dict) else {}
    return {
        "id": str(row.id),
        "request_id": row.request_id,
        "action": metadata_json.get("action"),
        "target_type": metadata_json.get("target_type"),
        "target_id": metadata_json.get("target_id"),
        "method": row.method,
        "path": row.path,
        "status_code": row.status_code,
        "created_at": row.created_at.isoformat(),
        "user_id": str(row.user_id) if row.user_id else None,
    }


@router.get("")
async def get_audit_logs(
    request: Request,
    project_id: str | None = None,
    action: str | None = Query(None),
    target_type: str | None = Query(None),
    target_id: str | None = Query(None),
    method: str | None = Query(None),
    status_code: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session_factory = require_db_session_factory(request)
    normalized_action = (
        action.strip() if isinstance(action, str) and action.strip() else None
    )
    normalized_target_type = (
        target_type.strip()
        if isinstance(target_type, str) and target_type.strip()
        else None
    )
    normalized_target_id = (
        target_id.strip() if isinstance(target_id, str) and target_id.strip() else None
    )
    normalized_method = (
        method.strip().upper() if isinstance(method, str) and method.strip() else None
    )
    normalized_status_code = (
        status_code if isinstance(status_code, int) and status_code > 0 else None
    )

    if project_id is None or not project_id.strip():
        actor_user_id = current_user_id_from_request(request)
        if not user_has_admin_capability(request, actor_user_id):
            raise HTTPException(status_code=403, detail="admin_required")
        with session_scope(session_factory) as session:
            rows, _ = list_audit_logs(session, limit=5000, offset=0)
            filtered_rows = [
                row
                for row in rows
                if (
                    normalized_method is None or row.method.upper() == normalized_method
                )
                and (
                    normalized_status_code is None
                    or row.status_code == normalized_status_code
                )
                and _matches_metadata_filters(
                    row.metadata_json,
                    action=normalized_action,
                    target_type=normalized_target_type,
                    target_id=normalized_target_id,
                )
            ]
            page_rows = filtered_rows[offset : offset + limit]
            return {
                "items": [_serialize_audit_row(row) for row in page_rows],
                "total": len(filtered_rows),
            }

    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")

    require_project_role(request, project_uuid, allowed_roles={"admin", "editor"})
    with session_scope(session_factory) as session:
        rows, _ = list_audit_logs_for_project(
            session, project_uuid, limit=5000, offset=0
        )
        filtered_rows = [
            row
            for row in rows
            if (normalized_method is None or row.method.upper() == normalized_method)
            and (
                normalized_status_code is None
                or row.status_code == normalized_status_code
            )
            and _matches_metadata_filters(
                row.metadata_json,
                action=normalized_action,
                target_type=normalized_target_type,
                target_id=normalized_target_id,
            )
        ]
        page_rows = filtered_rows[offset : offset + limit]
        return {
            "items": [_serialize_audit_row(row) for row in page_rows],
            "total": len(filtered_rows),
        }
