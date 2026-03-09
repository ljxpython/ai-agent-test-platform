from __future__ import annotations

from typing import Any

from app.services.langgraph_sdk.graphs_service import LangGraphGraphsService
from fastapi import APIRouter, Body, Request
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/graphs")


@router.post("/search")
async def search_graphs(request: Request, payload: dict[str, Any] = Body(...)) -> Any:
    service = LangGraphGraphsService(request)
    result = await service.search(payload)
    return jsonable_encoder(result)


@router.post("/count")
async def count_graphs(request: Request, payload: dict[str, Any] = Body(...)) -> Any:
    service = LangGraphGraphsService(request)
    result = await service.count(payload)
    return jsonable_encoder(result)
