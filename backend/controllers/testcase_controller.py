"""
测试用例控制器
"""

from typing import List, Optional

from backend.core.crud import CRUDBase
from backend.models.testcase import TestCaseConversation
from backend.schemas.base import Fail, Success
from backend.services.testcase.testcase_service import testcase_service


class TestCaseController(CRUDBase[TestCaseConversation, dict, dict]):
    """测试用例控制器类"""

    def __init__(self):
        super().__init__(TestCaseConversation)
        self.testcase_service = testcase_service

    async def upload_file(self, file, conversation_id: str):
        """文件上传"""
        try:
            result = await self.testcase_service.upload_file(file, conversation_id)
            return Success(data=result, msg="文件上传成功")
        except Exception as e:
            return Fail(msg=f"文件上传失败: {str(e)}")

    async def start_streaming_generation(self, requirement):
        """启动流式生成"""
        try:
            await self.testcase_service.start_streaming_generation(requirement)
            return Success(msg="生成任务已启动")
        except Exception as e:
            return Fail(msg=f"启动生成失败: {str(e)}")

    async def submit_feedback(self, conversation_id: str, feedback: str):
        """提交用户反馈"""
        try:
            await self.testcase_service.submit_feedback(conversation_id, feedback)
            return Success(msg="反馈已提交")
        except Exception as e:
            return Fail(msg=f"提交反馈失败: {str(e)}")

    async def get_history(self, conversation_id: str):
        """获取对话历史"""
        try:
            history = await self.testcase_service.get_history(conversation_id)
            return Success(data=history, msg="获取历史成功")
        except Exception as e:
            return Fail(msg=f"获取历史失败: {str(e)}")

    async def get_messages(self, conversation_id: str):
        """获取消息列表"""
        try:
            messages = self.testcase_service.get_messages(conversation_id)
            return Success(data=messages, msg="获取消息成功")
        except Exception as e:
            return Fail(msg=f"获取消息失败: {str(e)}")

    async def clear_conversation(self, conversation_id: str):
        """清除对话历史"""
        try:
            await self.testcase_service.clear_conversation(conversation_id)
            return Success(msg="对话历史已清除")
        except Exception as e:
            return Fail(msg=f"清除历史失败: {str(e)}")


# 创建全局实例
testcase_controller = TestCaseController()
