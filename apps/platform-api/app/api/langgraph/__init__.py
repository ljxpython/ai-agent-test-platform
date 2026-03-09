from __future__ import annotations

from app.api.langgraph.assistants import router as assistants_router
from app.api.langgraph.graphs import router as graphs_router
from app.api.langgraph.info import router as info_router
from app.api.langgraph.runs import router as runs_router
from app.api.langgraph.threads import router as threads_router
from fastapi import APIRouter

router = APIRouter(prefix="/api/langgraph", tags=["langgraph-sdk"])
router.include_router(info_router)
router.include_router(assistants_router)
router.include_router(graphs_router)
router.include_router(threads_router)
router.include_router(runs_router)
