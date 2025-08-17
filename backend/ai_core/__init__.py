"""
AI核心组件模块

该模块包含大模型应用开发中的常用组件：
- LLM客户端管理
- 智能体基础类和工厂
- 运行时管理器
- 内存管理器
- BMAD框架集成组件
- 提示词模板（计划中）
- 工具函数（计划中）
"""

# 智能体基础类

# 智能体工厂
from .factory import (
    AgentFactory,
    AgentType,
    create_assistant_agent,
    create_user_proxy_agent,
    get_agent_factory,
)

# LLM客户端管理
from .llm import get_openai_model_client  # 向后兼容
from .llm import (
    LLMClientManager,
    ModelType,
    get_deepseek_client,
    get_default_client,
    get_model_config_status,
    get_qwen_vl_client,
    get_ui_tars_client,
    validate_model_configs,
)

# 内存管理
from .memory import ConversationMemory, MemoryManager, get_memory_manager

# 多模态消息处理
from .multimodal import (
    MultiModalProcessor,
    create_multimodal_message,
    create_text_message,
    load_image_from_base64,
    load_image_from_bytes,
    load_image_from_file,
)

# 运行时管理
from .runtime import BaseRuntime, MessageQueue, RuntimeState

__all__ = [
    # LLM客户端
    "get_deepseek_client",
    "get_qwen_vl_client",
    "get_ui_tars_client",
    "get_default_client",
    "validate_model_configs",
    "get_model_config_status",
    "get_openai_model_client",  # 向后兼容
    "LLMClientManager",
    "ModelType",
    # 智能体工厂
    "AgentType",
    "AgentFactory",
    "get_agent_factory",
    "create_assistant_agent",
    "create_user_proxy_agent",
    # 运行时管理
    "RuntimeState",
    "MessageQueue",
    "BaseRuntime",
    # 内存管理
    "ConversationMemory",
    "MemoryManager",
    "get_memory_manager",
    # 多模态消息处理
    "MultiModalProcessor",
    "create_multimodal_message",
    "create_text_message",
    "load_image_from_file",
    "load_image_from_bytes",
    "load_image_from_base64",
]
