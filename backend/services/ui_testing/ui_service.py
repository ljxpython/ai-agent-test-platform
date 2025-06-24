"""
UI测试服务
基于AI核心框架重构的UI测试服务实现
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from loguru import logger

# 使用AI核心框架
from backend.ai_core.llm import validate_model_configs
from backend.ai_core.memory import get_memory_manager
from backend.ai_core.message_queue import (
    get_streaming_sse_messages_from_queue,
    put_message_to_queue,
)
from backend.services.ui_testing.ui_runtime import get_ui_testing_runtime


class UITestingService:
    """UI测试服务 - 基于AI核心框架重构版本"""

    def __init__(self):
        """初始化服务"""
        self.runtime = get_ui_testing_runtime()
        self.memory_manager = get_memory_manager()

        logger.info("🎯 [UI测试服务] 基于AI核心框架的服务初始化完成")

    async def start_streaming_analysis(
        self, conversation_id: str, image_paths: List[str], user_requirement: str
    ) -> None:
        """
        启动流式UI测试分析

        Args:
            conversation_id: 对话ID
            image_paths: 图片路径列表
            user_requirement: 用户需求
        """
        logger.info(f"🌊 [UI测试服务] 启动流式分析 | 对话ID: {conversation_id}")
        logger.info(f"📷 图片数量: {len(image_paths)}")
        logger.info(f"📝 用户需求: {user_requirement[:100]}...")

        try:
            # 验证模型配置
            configs = validate_model_configs()
            if not any(configs.values()):
                error_msg = "没有可用的模型配置"
                logger.error(f"❌ [UI测试服务] {error_msg}")
                await put_message_to_queue(
                    conversation_id,
                    json.dumps(
                        {
                            "type": "error",
                            "source": "system",
                            "content": error_msg,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                    ),
                )
                return

            # 验证图片文件
            valid_image_paths = []
            for image_path in image_paths:
                if Path(image_path).exists():
                    valid_image_paths.append(image_path)
                    logger.debug(f"✅ 图片文件验证通过: {image_path}")
                else:
                    logger.warning(f"⚠️ 图片文件不存在: {image_path}")

            if not valid_image_paths:
                error_msg = "没有有效的图片文件"
                logger.error(f"❌ [UI测试服务] {error_msg}")
                await put_message_to_queue(
                    conversation_id,
                    json.dumps(
                        {
                            "type": "error",
                            "source": "system",
                            "content": error_msg,
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat(),
                        },
                        ensure_ascii=False,
                    ),
                )
                return

            logger.info(f"✅ 验证通过，有效图片数量: {len(valid_image_paths)}")

            # 初始化运行时
            await self.runtime.initialize_runtime(conversation_id)

            # 发送系统开始消息
            await put_message_to_queue(
                conversation_id,
                json.dumps(
                    {
                        "type": "system_start",
                        "message": "四智能体协作分析开始",
                        "content": "正在启动UI分析、交互分析、Midscene生成和脚本生成智能体...",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                ),
            )

            # 启动UI分析
            await self.runtime.start_ui_analysis(
                conversation_id, valid_image_paths, user_requirement
            )

            # 保存分析请求到内存
            await self.memory_manager.save_to_memory(
                conversation_id,
                {
                    "type": "ui_analysis_request",
                    "image_paths": valid_image_paths,
                    "user_requirement": user_requirement,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.success(
                f"✅ [UI测试服务] 流式分析启动成功 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 流式分析启动失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

            # 发送错误消息
            await put_message_to_queue(
                conversation_id,
                json.dumps(
                    {
                        "type": "system_error",
                        "message": "系统启动失败",
                        "content": f"UI测试分析启动失败: {str(e)}",
                        "conversation_id": conversation_id,
                        "timestamp": datetime.now().isoformat(),
                    },
                    ensure_ascii=False,
                ),
            )
            raise

    async def get_streaming_response(self, conversation_id: str):
        """
        获取流式响应

        Args:
            conversation_id: 对话ID

        Returns:
            异步生成器，产生SSE格式的消息
        """
        logger.info(f"📡 [UI测试服务] 获取流式响应 | 对话ID: {conversation_id}")

        try:
            # 使用AI核心框架的流式SSE消息获取函数（内部已有300秒超时）
            async for message in get_streaming_sse_messages_from_queue(conversation_id):
                yield message

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 流式响应获取失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            # 发送错误消息
            error_message = f"data: {json.dumps({'type': 'error', 'content': f'流式响应获取失败: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield error_message

    async def cleanup_conversation(self, conversation_id: str) -> None:
        """
        清理对话资源

        Args:
            conversation_id: 对话ID
        """
        logger.info(f"🗑️ [UI测试服务] 清理对话资源 | 对话ID: {conversation_id}")

        try:
            # 清理运行时（包括队列）
            await self.runtime.cleanup_runtime(conversation_id)

            logger.success(
                f"✅ [UI测试服务] 对话资源清理完成 | 对话ID: {conversation_id}"
            )

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 对话资源清理失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

    async def get_conversation_history(self, conversation_id: str) -> List[dict]:
        """
        获取对话历史

        Args:
            conversation_id: 对话ID

        Returns:
            对话历史列表
        """
        logger.info(f"📚 [UI测试服务] 获取对话历史 | 对话ID: {conversation_id}")

        try:
            # 使用内存管理器获取对话历史
            memory = await self.memory_manager.get_memory(conversation_id)
            if memory:
                history = await memory.get_messages()
                logger.info(f"📖 获取到 {len(history)} 条历史记录")
                return history
            else:
                logger.info("📭 没有找到对话历史")
                return []

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 获取对话历史失败 | 对话ID: {conversation_id} | 错误: {e}"
            )
            return []

    async def save_analysis_result(
        self, conversation_id: str, result_type: str, content: str
    ) -> None:
        """
        保存分析结果

        Args:
            conversation_id: 对话ID
            result_type: 结果类型
            content: 结果内容
        """
        logger.info(
            f"💾 [UI测试服务] 保存分析结果 | 对话ID: {conversation_id} | 类型: {result_type}"
        )

        try:
            await self.memory_manager.save_to_memory(
                conversation_id,
                {
                    "type": result_type,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                },
            )

            logger.success(f"✅ 分析结果已保存 | 类型: {result_type}")

        except Exception as e:
            logger.error(
                f"❌ [UI测试服务] 保存分析结果失败 | 对话ID: {conversation_id} | 错误: {e}"
            )

    def get_service_status(self) -> dict:
        """
        获取服务状态

        Returns:
            服务状态信息
        """
        try:
            configs = validate_model_configs()
            return {
                "service_name": "UI测试服务",
                "status": "running",
                "framework": "AI核心框架",
                "model_configs": configs,
                "runtime_status": "initialized",
                "memory_manager": "available",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"❌ [UI测试服务] 获取服务状态失败: {e}")
            return {
                "service_name": "UI测试服务",
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# 创建全局服务实例
ui_testing_service = UITestingService()

# 导出接口
__all__ = [
    "UITestingService",
    "ui_testing_service",
]
