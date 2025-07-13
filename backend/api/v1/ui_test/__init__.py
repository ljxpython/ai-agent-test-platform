"""
UI测试相关API路由
"""

from fastapi import APIRouter
from loguru import logger

from .collections import ui_collections_router

# 导入各个UI测试子模块
from .image_analysis import ui_image_analysis_router
from .rag_query import ui_rag_query_router
from .upload import ui_upload_router

# 创建UI测试主路由
ui_test_router = APIRouter()

# 注册子路由
ui_test_router.include_router(ui_upload_router, tags=["UI图片上传"])
ui_test_router.include_router(
    ui_image_analysis_router, prefix="/image-analysis", tags=["UI图片分析"]
)
ui_test_router.include_router(
    ui_rag_query_router, prefix="/rag-query", tags=["UI测试RAG查询"]
)
ui_test_router.include_router(
    ui_collections_router, prefix="/collections", tags=["UI测试Collection管理"]
)

logger.info("🔧 UI测试API路由模块初始化完成")

__all__ = ["ui_test_router"]
