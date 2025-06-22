"""
聊天控制器
"""

from typing import Optional

from backend.core.crud import CRUDBase
from backend.models.chat import ChatMessage
from backend.schemas.base import Fail, Success
from backend.services.ai_chat.autogen_service import autogen_service


class ChatController(CRUDBase[ChatMessage, dict, dict]):
    """聊天控制器类"""

    def __init__(self):
        super().__init__(ChatMessage)
        self.autogen_service = autogen_service

    async def chat_stream(
        self, message: str, conversation_id: str, system_message: Optional[str] = None
    ):
        """流式聊天"""
        try:
            async for chunk in self.autogen_service.chat_stream(
                message=message,
                conversation_id=conversation_id,
                system_message=system_message,
            ):
                yield chunk
        except Exception as e:
            yield f"错误: {str(e)}"

    async def chat(
        self, message: str, conversation_id: str, system_message: Optional[str] = None
    ):
        """普通聊天"""
        try:
            response_message, conv_id = await self.autogen_service.chat(
                message=message,
                conversation_id=conversation_id,
                system_message=system_message,
            )
            return Success(
                data={"message": response_message, "conversation_id": conv_id},
                msg="聊天成功",
            )
        except Exception as e:
            return Fail(msg=f"聊天失败: {str(e)}")

    async def clear_conversation(self, conversation_id: str):
        """清除对话历史"""
        try:
            self.autogen_service.clear_conversation(conversation_id)
            return Success(msg="对话已清除")
        except Exception as e:
            return Fail(msg=f"清除对话失败: {str(e)}")

    async def get_agent_stats(self):
        """获取Agent统计信息"""
        try:
            stats = self.autogen_service.get_agent_stats()
            return Success(data=stats, msg="获取统计信息成功")
        except Exception as e:
            return Fail(msg=f"获取统计信息失败: {str(e)}")

    async def force_cleanup(self):
        """强制清理过期Agent"""
        try:
            self.autogen_service.force_cleanup()
            stats = self.autogen_service.get_agent_stats()
            return Success(data={"stats": stats}, msg="清理完成")
        except Exception as e:
            return Fail(msg=f"清理失败: {str(e)}")


# 创建全局实例
chat_controller = ChatController()
