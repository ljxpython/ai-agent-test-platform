"""
权限管理服务
"""

from typing import Any, Dict, List

from fastapi import FastAPI
from loguru import logger

from backend.models.api import Api
from backend.models.role import Role


class PermissionService:
    """权限管理服务"""

    @staticmethod
    async def sync_apis_from_app(app: FastAPI) -> Dict[str, Any]:
        """从FastAPI应用同步API权限"""
        try:
            synced_count = 0
            updated_count = 0

            # 获取所有路由
            routes = []
            for route in app.routes:
                if hasattr(route, "methods") and hasattr(route, "path"):
                    for method in route.methods:
                        if method not in ["HEAD", "OPTIONS"]:  # 排除HEAD和OPTIONS
                            routes.append(
                                {
                                    "path": route.path,
                                    "method": method,
                                    "summary": getattr(route, "summary", ""),
                                    "description": getattr(route, "description", ""),
                                    "tags": getattr(route, "tags", []),
                                }
                            )

            logger.info(f"从应用中发现 {len(routes)} 个API路由")

            # 同步到数据库
            for route_info in routes:
                path = route_info["path"]
                method = route_info["method"]

                # 检查API是否已存在
                existing_api = await Api.get_or_none(path=path, method=method)

                if existing_api:
                    # 更新现有API
                    updated = False
                    if existing_api.summary != route_info["summary"]:
                        existing_api.summary = route_info["summary"]
                        updated = True
                    if existing_api.description != route_info["description"]:
                        existing_api.description = route_info["description"]
                        updated = True
                    if existing_api.tags != ",".join(route_info["tags"]):
                        existing_api.tags = ",".join(route_info["tags"])
                        updated = True

                    if updated:
                        await existing_api.save()
                        updated_count += 1
                        logger.debug(f"更新API: {method} {path}")
                else:
                    # 创建新API
                    await Api.create(
                        path=path,
                        method=method,
                        summary=route_info["summary"],
                        description=route_info["description"],
                        tags=",".join(route_info["tags"]),
                        is_active=True,
                    )
                    synced_count += 1
                    logger.debug(f"新增API: {method} {path}")

            logger.success(
                f"API同步完成: 新增 {synced_count} 个，更新 {updated_count} 个"
            )

            return {
                "synced_count": synced_count,
                "updated_count": updated_count,
                "total_routes": len(routes),
            }

        except Exception as e:
            logger.error(f"API同步失败: {e}")
            raise

    @staticmethod
    async def get_user_permissions(user_id: int) -> List[Dict[str, str]]:
        """获取用户权限列表"""
        try:
            from backend.models.user import User

            user = await User.get_or_none(id=user_id).prefetch_related("roles__apis")
            if not user:
                return []

            if user.is_superuser:
                # 超级用户拥有所有权限
                apis = await Api.filter(is_active=True).all()
                return [{"method": api.method, "path": api.path} for api in apis]

            # 普通用户根据角色获取权限
            permissions = set()
            for role in user.roles:
                if role.is_active:
                    for api in role.apis:
                        if api.is_active:
                            permissions.add((api.method, api.path))

            return [{"method": method, "path": path} for method, path in permissions]

        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return []

    @staticmethod
    async def assign_role_permissions(role_id: int, api_ids: List[int]) -> bool:
        """为角色分配API权限"""
        try:
            role = await Role.get_or_none(id=role_id)
            if not role:
                logger.error(f"角色不存在: {role_id}")
                return False

            # 清除现有权限
            await role.apis.clear()

            # 分配新权限
            if api_ids:
                apis = await Api.filter(id__in=api_ids, is_active=True).all()
                for api in apis:
                    await role.apis.add(api)

            logger.info(f"为角色 {role.name} 分配了 {len(api_ids)} 个API权限")
            return True

        except Exception as e:
            logger.error(f"分配角色权限失败: {e}")
            return False

    @staticmethod
    async def get_role_permissions(role_id: int) -> List[int]:
        """获取角色的API权限ID列表"""
        try:
            role = await Role.get_or_none(id=role_id).prefetch_related("apis")
            if not role:
                return []

            return [api.id for api in role.apis if api.is_active]

        except Exception as e:
            logger.error(f"获取角色权限失败: {e}")
            return []

    @staticmethod
    async def init_default_permissions():
        """初始化默认权限"""
        try:
            # 为管理员角色分配所有权限
            admin_role = await Role.get_or_none(name="管理员")
            if admin_role:
                all_apis = await Api.filter(is_active=True).all()
                await admin_role.apis.clear()
                for api in all_apis:
                    await admin_role.apis.add(api)

                logger.info(f"为管理员角色分配了 {len(all_apis)} 个API权限")

        except Exception as e:
            logger.error(f"初始化默认权限失败: {e}")


# 创建服务实例
permission_service = PermissionService()
