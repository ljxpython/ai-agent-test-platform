from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.dependency import (
    AdminPermissionControl,
    AuthControl,
    PermissionControl,
)
from backend.core.security import decode_access_token
from backend.models.user import User
from backend.services.auth.auth_service import AuthService

auth_service = AuthService()

# HTTP Bearer 认证
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 解码令牌
        token_data = decode_access_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception

        user_id = token_data.get("user_id")
        if user_id is None:
            raise credentials_exception

        # 获取用户
        user = await auth_service.get_user_by_id(user_id)
        if user is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用"
            )

        return user

    except HTTPException:
        raise
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户已被禁用"
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_user)) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="权限不足")
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    """获取可选的当前用户（用于可选认证的接口）"""
    if not credentials:
        return None

    try:
        token_data = decode_access_token(credentials.credentials)
        if token_data is None:
            return None

        user_id = token_data.get("user_id")
        if user_id is None:
            return None

        user = await auth_service.get_user_by_id(user_id)
        if user is None or not user.is_active:
            return None

        return user

    except Exception:
        return None


# 新的权限管理依赖注入（推荐使用）
get_current_user_new = Depends(AuthControl.is_authed)
require_permission = Depends(PermissionControl.has_permission)
require_admin = Depends(AdminPermissionControl.is_admin)

# 向后兼容的别名
get_current_active_user_new = get_current_user_new
get_current_superuser_new = require_admin
