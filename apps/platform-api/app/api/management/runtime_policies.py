from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.api.management.common import require_db_session_factory, require_project_role
from app.api.management.schemas import (
    UpsertProjectGraphPolicyRequest,
    UpsertProjectModelPolicyRequest,
    UpsertProjectToolPolicyRequest,
)
from app.db.access import (
    list_project_graph_policies,
    list_project_model_policies,
    list_project_tool_policies,
    list_runtime_graph_catalog_items,
    list_runtime_model_catalog_items,
    list_runtime_tool_catalog_items,
    parse_uuid,
    upsert_project_graph_policy,
    upsert_project_model_policy,
    upsert_project_tool_policy,
)
from app.db.models import RuntimeCatalogGraph, RuntimeCatalogModel, RuntimeCatalogTool
from app.db.session import session_scope
from fastapi import APIRouter, HTTPException, Request

router = APIRouter(tags=["management-runtime-policies"])


def _runtime_id(request: Request) -> str:
    return request.app.state.settings.langgraph_upstream_url.rstrip("/")


@router.get("/projects/{project_id}/graph-policies")
async def get_project_graph_policies(
    request: Request, project_id: str
) -> dict[str, Any]:
    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor", "executor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        catalog_rows = list_runtime_graph_catalog_items(
            session, runtime_id=_runtime_id(request)
        )
        policy_rows = list_project_graph_policies(session, project_id=project_uuid)
    policy_map = {str(row.graph_catalog_id): row for row in policy_rows}
    items = []
    for row in catalog_rows:
        policy = policy_map.get(str(row.id))
        items.append(
            {
                "catalog_id": str(row.id),
                "graph_id": row.graph_key,
                "display_name": row.display_name or row.graph_key,
                "description": row.description or "",
                "source_type": row.source_type,
                "sync_status": row.sync_status,
                "last_synced_at": row.last_synced_at,
                "policy": {
                    "is_enabled": policy.is_enabled if policy else True,
                    "display_order": policy.display_order if policy else None,
                    "note": policy.note if policy else None,
                },
            }
        )
    return {"items": items, "total": len(items)}


@router.put("/projects/{project_id}/graph-policies/{catalog_id}")
async def put_project_graph_policy(
    request: Request,
    project_id: str,
    catalog_id: str,
    payload: UpsertProjectGraphPolicyRequest,
) -> dict[str, Any]:
    project_uuid = parse_uuid(project_id)
    catalog_uuid = parse_uuid(catalog_id)
    if project_uuid is None or catalog_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_id")
    actor_user_id, _ = require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        if session.get(RuntimeCatalogGraph, catalog_uuid) is None:
            raise HTTPException(status_code=404, detail="graph_catalog_not_found")
        row = upsert_project_graph_policy(
            session,
            project_id=project_uuid,
            graph_catalog_id=catalog_uuid,
            is_enabled=payload.is_enabled,
            display_order=payload.display_order,
            note=payload.note,
            updated_by=actor_user_id,
        )
        return {
            "catalog_id": str(row.graph_catalog_id),
            "project_id": str(row.project_id),
            "is_enabled": row.is_enabled,
            "display_order": row.display_order,
            "note": row.note,
            "updated_at": row.updated_at,
        }


@router.get("/projects/{project_id}/model-policies")
async def get_project_model_policies(
    request: Request, project_id: str
) -> dict[str, Any]:
    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor", "executor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        catalog_rows = list_runtime_model_catalog_items(
            session, runtime_id=_runtime_id(request)
        )
        policy_rows = list_project_model_policies(session, project_id=project_uuid)
    policy_map = {str(row.model_catalog_id): row for row in policy_rows}
    items = []
    for row in catalog_rows:
        policy = policy_map.get(str(row.id))
        items.append(
            {
                "catalog_id": str(row.id),
                "model_id": row.model_key,
                "display_name": row.display_name or row.model_key,
                "is_default_runtime": row.is_default_runtime,
                "sync_status": row.sync_status,
                "last_synced_at": row.last_synced_at,
                "policy": {
                    "is_enabled": policy.is_enabled if policy else True,
                    "is_default_for_project": (
                        policy.is_default_for_project if policy else False
                    ),
                    "temperature_default": (
                        float(policy.temperature_default)
                        if policy and policy.temperature_default is not None
                        else None
                    ),
                    "note": policy.note if policy else None,
                },
            }
        )
    return {"items": items, "total": len(items)}


@router.put("/projects/{project_id}/model-policies/{catalog_id}")
async def put_project_model_policy(
    request: Request,
    project_id: str,
    catalog_id: str,
    payload: UpsertProjectModelPolicyRequest,
) -> dict[str, Any]:
    project_uuid = parse_uuid(project_id)
    catalog_uuid = parse_uuid(catalog_id)
    if project_uuid is None or catalog_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_id")
    actor_user_id, _ = require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        if session.get(RuntimeCatalogModel, catalog_uuid) is None:
            raise HTTPException(status_code=404, detail="model_catalog_not_found")
        row = upsert_project_model_policy(
            session,
            project_id=project_uuid,
            model_catalog_id=catalog_uuid,
            is_enabled=payload.is_enabled,
            is_default_for_project=payload.is_default_for_project,
            temperature_default=(
                Decimal(str(payload.temperature_default))
                if payload.temperature_default is not None
                else None
            ),
            note=payload.note,
            updated_by=actor_user_id,
        )
        return {
            "catalog_id": str(row.model_catalog_id),
            "project_id": str(row.project_id),
            "is_enabled": row.is_enabled,
            "is_default_for_project": row.is_default_for_project,
            "temperature_default": (
                float(row.temperature_default)
                if row.temperature_default is not None
                else None
            ),
            "note": row.note,
            "updated_at": row.updated_at,
        }


@router.get("/projects/{project_id}/tool-policies")
async def get_project_tool_policies(
    request: Request, project_id: str
) -> dict[str, Any]:
    project_uuid = parse_uuid(project_id)
    if project_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_project_id")
    require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor", "executor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        catalog_rows = list_runtime_tool_catalog_items(
            session, runtime_id=_runtime_id(request)
        )
        policy_rows = list_project_tool_policies(session, project_id=project_uuid)
    policy_map = {str(row.tool_catalog_id): row for row in policy_rows}
    items = []
    for row in catalog_rows:
        policy = policy_map.get(str(row.id))
        items.append(
            {
                "catalog_id": str(row.id),
                "tool_key": row.tool_key,
                "name": row.name,
                "source": row.source or "",
                "description": row.description or "",
                "sync_status": row.sync_status,
                "last_synced_at": row.last_synced_at,
                "policy": {
                    "is_enabled": policy.is_enabled if policy else True,
                    "display_order": policy.display_order if policy else None,
                    "note": policy.note if policy else None,
                },
            }
        )
    return {"items": items, "total": len(items)}


@router.put("/projects/{project_id}/tool-policies/{catalog_id}")
async def put_project_tool_policy(
    request: Request,
    project_id: str,
    catalog_id: str,
    payload: UpsertProjectToolPolicyRequest,
) -> dict[str, Any]:
    project_uuid = parse_uuid(project_id)
    catalog_uuid = parse_uuid(catalog_id)
    if project_uuid is None or catalog_uuid is None:
        raise HTTPException(status_code=400, detail="invalid_id")
    actor_user_id, _ = require_project_role(
        request, project_uuid, allowed_roles={"admin", "editor"}
    )
    session_factory = require_db_session_factory(request)
    with session_scope(session_factory) as session:
        if session.get(RuntimeCatalogTool, catalog_uuid) is None:
            raise HTTPException(status_code=404, detail="tool_catalog_not_found")
        row = upsert_project_tool_policy(
            session,
            project_id=project_uuid,
            tool_catalog_id=catalog_uuid,
            is_enabled=payload.is_enabled,
            display_order=payload.display_order,
            note=payload.note,
            updated_by=actor_user_id,
        )
        return {
            "catalog_id": str(row.tool_catalog_id),
            "project_id": str(row.project_id),
            "is_enabled": row.is_enabled,
            "display_order": row.display_order,
            "note": row.note,
            "updated_at": row.updated_at,
        }
