"""Scaffold router for SDK-backed threads endpoints."""

from __future__ import annotations

from typing import Any

from app.services.langgraph_sdk.scope_guard import (
    assert_thread_belongs_project,
    inject_project_metadata,
)
from app.services.langgraph_sdk.threads_service import LangGraphThreadsService
from fastapi import APIRouter, Body, Query, Request
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/threads")


@router.post("")
async def create_thread(request: Request, payload: dict[str, Any] = Body(...)) -> Any:
    """
    创建 thread 资源。

    参数说明：
    - request: 当前 HTTP 请求上下文，用于构造 SDK 客户端。
    - payload: 创建参数对象，常见字段包括 metadata、thread_id、if_exists、supersteps、graph_id、ttl。

    返回语义：
    - 返回上游创建后的 thread 对象（已序列化）。
    """
    scoped_payload = inject_project_metadata(request, payload)
    service = LangGraphThreadsService(request)
    thread = await service.create(scoped_payload)
    return jsonable_encoder(thread)


@router.post("/search")
async def search_threads(request: Request, payload: dict[str, Any] = Body(...)) -> Any:
    """
    按条件检索 threads 列表。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - payload: 检索过滤与分页参数，主要字段包括 metadata、values、ids、status、limit、offset、sort_by、sort_order、select、extract。

    返回语义：
    - 返回符合过滤条件的 thread 列表或上游定义的数据结构（已序列化）。
    """
    scoped_payload = inject_project_metadata(request, payload)
    service = LangGraphThreadsService(request)
    threads = await service.search(scoped_payload)
    return jsonable_encoder(threads)


@router.post("/count")
async def count_threads(request: Request, payload: dict[str, Any] = Body(...)) -> Any:
    """
    统计符合条件的 threads 数量。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - payload: 计数过滤参数，主要字段包括 metadata、values、status。

    返回语义：
    - 返回上游 count 接口结果（通常包含总数信息，已序列化）。
    """
    scoped_payload = inject_project_metadata(request, payload)
    service = LangGraphThreadsService(request)
    count = await service.count(scoped_payload)
    return jsonable_encoder(count)


@router.post("/prune")
async def prune_threads(request: Request, payload: dict[str, Any] = Body(...)) -> Any:
    """
    批量清理 threads。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - payload: 清理参数，主要字段包括 thread_ids（待处理 ID 列表）和 strategy（清理策略）。

    返回语义：
    - 返回上游 prune 操作结果（已序列化）。
    """
    thread_ids = payload.get("thread_ids")
    if isinstance(thread_ids, list):
        for thread_id in thread_ids:
            if isinstance(thread_id, str) and thread_id:
                await assert_thread_belongs_project(request, thread_id)

    service = LangGraphThreadsService(request)
    result = await service.prune(payload)
    return jsonable_encoder(result)


@router.get("/{thread_id}")
async def get_thread(request: Request, thread_id: str) -> Any:
    """
    按 thread_id 获取单个 thread 详情。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: thread 的唯一标识。

    返回语义：
    - 返回对应 thread 的详细信息（已序列化）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    thread = await service.get(thread_id)
    return jsonable_encoder(thread)


@router.patch("/{thread_id}")
async def update_thread(
    request: Request, thread_id: str, payload: dict[str, Any] = Body(...)
) -> Any:
    """
    更新指定 thread 的可变字段。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 目标 thread 的唯一标识。
    - payload: 更新参数对象，主要字段包括 metadata、ttl。

    返回语义：
    - 返回更新后的 thread 对象（已序列化）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    thread = await service.update(thread_id, payload)
    return jsonable_encoder(thread)


@router.delete("/{thread_id}")
async def delete_thread(request: Request, thread_id: str) -> Any:
    """
    删除指定 thread。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 要删除的 thread 标识。

    返回语义：
    - 若上游返回具体结果，则透传并序列化该结果。
    - 若上游返回 None，则回退为 {"ok": true} 语义（本实现中为 Python 布尔值 True）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    result = await service.delete(thread_id)
    if result is None:
        return {"ok": True}
    return jsonable_encoder(result)


@router.post("/{thread_id}/copy")
async def copy_thread(request: Request, thread_id: str) -> Any:
    """
    复制指定 thread。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 要复制的源 thread 标识。

    返回语义：
    - 若上游返回复制结果，则透传并序列化该结果。
    - 若上游返回 None，则回退为 {"ok": true} 语义（本实现中为 Python 布尔值 True）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    result = await service.copy(thread_id)
    if result is None:
        return {"ok": True}
    return jsonable_encoder(result)


@router.get("/{thread_id}/state")
async def get_thread_state(
    request: Request,
    thread_id: str,
    subgraphs: bool | None = Query(default=None),
    checkpoint_id: str | None = Query(default=None),
) -> Any:
    """
    获取 thread 当前状态或指定 checkpoint 的状态视图。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 目标 thread 标识。
    - subgraphs: 可选，是否包含子图状态信息。
    - checkpoint_id: 可选，指定要读取的 checkpoint 标识。

    返回语义：
    - 返回线程状态对象；仅在传入参数时才向上游转发对应字段（已序列化）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    state_payload: dict[str, Any] = {}
    if subgraphs is not None:
        state_payload["subgraphs"] = subgraphs
    if checkpoint_id is not None:
        state_payload["checkpoint_id"] = checkpoint_id
    state = await service.get_state(thread_id, state_payload)
    return jsonable_encoder(state)


@router.post("/{thread_id}/state")
async def update_thread_state(
    request: Request,
    thread_id: str,
    payload: dict[str, Any] = Body(...),
) -> Any:
    """
    更新 thread 状态。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 目标 thread 标识。
    - payload: 状态更新参数，主要字段包括 values、as_node、checkpoint、checkpoint_id。

    返回语义：
    - 返回上游更新后的状态结果（已序列化）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    state = await service.update_state(thread_id, payload)
    return jsonable_encoder(state)


@router.get("/{thread_id}/state/{checkpoint_id}")
async def get_thread_state_at_checkpoint(
    request: Request,
    thread_id: str,
    checkpoint_id: str,
) -> Any:
    """
    按 checkpoint_id 获取 thread 在历史检查点的状态。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 目标 thread 标识。
    - checkpoint_id: 检查点标识。

    返回语义：
    - 返回指定检查点的状态快照（已序列化）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    state = await service.get_state_at_checkpoint(thread_id, checkpoint_id)
    return jsonable_encoder(state)


@router.post("/{thread_id}/history")
async def get_thread_history(
    request: Request,
    thread_id: str,
    payload: dict[str, Any] = Body(...),
) -> Any:
    """
    以 POST 方式查询 thread 历史记录。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 目标 thread 标识。
    - payload: 历史查询参数，主要字段包括 limit、before、metadata、checkpoint。

    返回语义：
    - 返回 thread 历史事件/检查点列表（已序列化）。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    history = await service.get_history(thread_id, payload)
    return jsonable_encoder(history)


@router.get("/{thread_id}/history")
async def get_thread_history_alias(
    request: Request,
    thread_id: str,
    limit: int | None = Query(default=None),
    before: str | None = Query(default=None),
) -> Any:
    """
    以 GET 方式查询 thread 历史记录（POST 历史接口别名）。

    参数说明：
    - request: 当前 HTTP 请求上下文。
    - thread_id: 目标 thread 标识。
    - limit: 可选，返回记录条数上限。
    - before: 可选，仅返回早于该游标/检查点的历史记录。

    返回语义：
    - 将查询参数组装为历史 payload 并复用历史查询服务，返回序列化后的历史结果。
    """
    await assert_thread_belongs_project(request, thread_id)
    service = LangGraphThreadsService(request)
    payload: dict[str, Any] = {}
    if limit is not None:
        payload["limit"] = limit
    if before is not None:
        payload["before"] = before
    history = await service.get_history(thread_id, payload)
    return jsonable_encoder(history)
