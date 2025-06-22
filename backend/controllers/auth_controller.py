"""
认证控制器
"""

from typing import Optional

from backend.core.crud import CRUDBase
from backend.models.user import User
from backend.schemas.base import Fail, Success
from backend.services.auth.auth_service import AuthService

auth_service = AuthService()


class AuthController(CRUDBase[User, dict, dict]):
    """认证控制器类"""

    def __init__(self):
        super().__init__(User)
        self.auth_service = auth_service

    async def login(self, username: str, password: str):
        """用户登录"""
        try:
            result = await self.auth_service.login_user(username, password)
            return Success(data=result, msg="登录成功")
        except Exception as e:
            return Fail(msg=f"登录失败: {str(e)}")

    async def register(self, username: str, email: str, password: str):
        """用户注册"""
        try:
            result = await self.auth_service.register_user(username, email, password)
            return Success(data=result, msg="注册成功")
        except Exception as e:
            return Fail(msg=f"注册失败: {str(e)}")

    async def get_current_user(self, token: str):
        """获取当前用户信息"""
        try:
            user = await self.auth_service.get_current_user(token)
            return Success(data=user, msg="获取用户信息成功")
        except Exception as e:
            return Fail(msg=f"获取用户信息失败: {str(e)}")


# 创建全局实例
auth_controller = AuthController()
