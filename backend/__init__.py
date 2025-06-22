"""
Backend package for AI Chat application
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.core.config_validator import validate_settings
from backend.core.exceptions import SettingNotFound
from backend.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)
from backend.core.logger import setup_logging

try:
    import os
    import sys

    from backend.conf.config import settings

    # 检测是否在生产环境或需要禁用颜色
    force_no_color = (
        os.getenv("FORCE_NO_COLOR") is not None
        or os.getenv("NO_COLOR") is not None
        or not hasattr(sys.stdout, "isatty")
        or not sys.stdout.isatty()
    )

    # 初始化日志系统
    setup_logging(
        log_level=getattr(settings, "LOG_LEVEL", "INFO"), force_no_color=force_no_color
    )

    # 验证配置
    validate_settings(settings)
except ImportError:
    raise SettingNotFound("Can not import settings")

__version__ = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    from loguru import logger

    # 启动时执行
    logger.info("🚀 应用启动中...")
    await init_data(app)
    logger.success("✅ 应用启动完成")

    yield

    # 关闭时执行
    logger.info("🛑 应用正在关闭...")
    logger.success("✅ 应用关闭完成")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    from loguru import logger

    logger.info("创建 FastAPI 应用...")

    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )

    # 注册异常处理器
    register_exceptions(app)

    # 注册路由
    register_routers(app, prefix="/api")

    logger.success(f"✅ FastAPI 应用创建完成: {settings.APP_TITLE} v{settings.VERSION}")
    return app


# 创建应用实例
app = create_app()
