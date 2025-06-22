"""
AI对话模块

该模块包含AI对话相关的服务：
- AutoGen智能体服务
"""

from .autogen_service import AutoGenService, autogen_service

__all__ = ["AutoGenService", "autogen_service"]
