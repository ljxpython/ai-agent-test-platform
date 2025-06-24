"""
UI测试模块
基于AI核心框架重构的UI测试智能体系统

该模块包含UI测试相关的服务：
- UI测试智能体实现
- UI测试专用运行时
- UI测试服务
- Midscene智能体服务（兼容性保留）
"""

from .agents import (
    InteractionAnalysisAgent,
    InteractionAnalysisMessage,
    MidsceneGenerationAgent,
    MidsceneGenerationMessage,
    ScriptGenerationAgent,
    ScriptGenerationMessage,
    UIAnalysisAgent,
    UIAnalysisMessage,
)
from .midscene_service import MidsceneService  # 兼容性保留
from .ui_runtime import UITestingRuntime, get_ui_testing_runtime
from .ui_service import UITestingService, ui_testing_service

__all__ = [
    # 新的基于AI核心框架的服务
    "UITestingService",
    "ui_testing_service",
    # 消息模型
    "UIAnalysisMessage",
    "InteractionAnalysisMessage",
    "MidsceneGenerationMessage",
    "ScriptGenerationMessage",
    # 运行时
    "UITestingRuntime",
    "get_ui_testing_runtime",
    # 智能体
    "UIAnalysisAgent",
    "InteractionAnalysisAgent",
    "MidsceneGenerationAgent",
    "ScriptGenerationAgent",
    # 兼容性保留
    "MidsceneService",
]
