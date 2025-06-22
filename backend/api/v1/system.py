"""
系统管理API路由
"""

from typing import List

from fastapi import APIRouter, HTTPException, Query, Request
from tortoise.expressions import Q

from backend.controllers.system_controller import (
    api_controller,
    department_controller,
    role_controller,
    user_controller,
)
from backend.schemas.base import Success, SuccessExtra
from backend.schemas.system import (
    ApiCreate,
    ApiResponse,
    ApiUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
    RoleUpdateApis,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from backend.services.auth.permission_service import permission_service

# 创建路由
system_router = APIRouter()

# ==================== 用户管理 ====================


@system_router.get("/users", summary="获取用户列表")
async def list_users(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名搜索"),
    email: str = Query("", description="邮箱搜索"),
    dept_id: int = Query(None, description="部门ID"),
):
    """获取用户列表"""
    q = Q()
    if username:
        q &= Q(username__icontains=username)
    if email:
        q &= Q(email__icontains=email)
    if dept_id is not None:
        q &= Q(dept_id=dept_id)

    total, users = await user_controller.list_with_dept_roles(
        page=page, page_size=page_size, search=q
    )

    # 转换为响应格式
    data = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
            "dept": {"id": user.dept.id, "name": user.dept.name} if user.dept else None,
            "roles": [{"id": role.id, "name": role.name} for role in user.roles],
        }
        data.append(user_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@system_router.get("/users/{user_id}", summary="获取用户详情")
async def get_user(user_id: int):
    """获取用户详情"""
    user = await user_controller.get(id=user_id)
    await user.fetch_related("dept", "roles")

    user_dict = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
        "dept_id": user.dept_id,
        "role_ids": [role.id for role in user.roles],
    }

    return Success(data=user_dict)


@system_router.post("/users", summary="创建用户")
async def create_user(user_in: UserCreate):
    """创建用户"""
    # 检查邮箱是否已存在
    if user_in.email and await user_controller.get_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="邮箱已存在")

    # 创建用户
    user = await user_controller.create_user(user_in)

    # 设置角色
    await user_controller.update_roles(user, user_in.role_ids)

    return Success(msg="用户创建成功")


@system_router.put("/users/{user_id}", summary="更新用户")
async def update_user(user_id: int, user_in: UserUpdate):
    """更新用户"""
    user_in.id = user_id

    # 更新用户基本信息
    user = await user_controller.update(id=user_id, obj_in=user_in)

    # 更新角色
    await user_controller.update_roles(user, user_in.role_ids)

    return Success(msg="用户更新成功")


@system_router.delete("/users/{user_id}", summary="删除用户")
async def delete_user(user_id: int):
    """删除用户"""
    await user_controller.remove(id=user_id)
    return Success(msg="用户删除成功")


@system_router.post("/users/{user_id}/reset-password", summary="重置用户密码")
async def reset_user_password(user_id: int):
    """重置用户密码"""
    await user_controller.reset_password(user_id)
    return Success(msg="密码已重置为123456")


# ==================== 角色管理 ====================


@system_router.get("/roles", summary="获取角色列表")
async def list_roles(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="角色名搜索"),
):
    """获取角色列表"""
    q = Q()
    if name:
        q &= Q(name__icontains=name)

    total, roles = await role_controller.list_with_apis(
        page=page, page_size=page_size, search=q
    )

    # 转换为响应格式
    data = []
    for role in roles:
        role_dict = {
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "is_active": role.is_active,
            "created_at": role.created_at.isoformat(),
            "updated_at": role.updated_at.isoformat(),
            "apis": [
                {"id": api.id, "path": api.path, "method": api.method}
                for api in role.apis
            ],
        }
        data.append(role_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@system_router.get("/roles/{role_id}", summary="获取角色详情")
async def get_role(role_id: int):
    """获取角色详情"""
    role = await role_controller.get(id=role_id)
    await role.fetch_related("apis")

    role_dict = {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "is_active": role.is_active,
        "created_at": role.created_at.isoformat(),
        "updated_at": role.updated_at.isoformat(),
        "api_ids": [api.id for api in role.apis],
    }

    return Success(data=role_dict)


@system_router.post("/roles", summary="创建角色")
async def create_role(role_in: RoleCreate):
    """创建角色"""
    # 检查角色名是否已存在
    if await role_controller.is_exist(role_in.name):
        raise HTTPException(status_code=400, detail="角色名已存在")

    await role_controller.create(obj_in=role_in)
    return Success(msg="角色创建成功")


@system_router.put("/roles/{role_id}", summary="更新角色")
async def update_role(role_id: int, role_in: RoleUpdate):
    """更新角色"""
    role_in.id = role_id
    await role_controller.update(id=role_id, obj_in=role_in)
    return Success(msg="角色更新成功")


@system_router.delete("/roles/{role_id}", summary="删除角色")
async def delete_role(role_id: int):
    """删除角色"""
    await role_controller.remove(id=role_id)
    return Success(msg="角色删除成功")


@system_router.put("/roles/{role_id}/apis", summary="更新角色API权限")
async def update_role_apis(role_id: int, role_apis: RoleUpdateApis):
    """更新角色API权限"""
    role = await role_controller.get(id=role_id)
    await role_controller.update_apis(role, role_apis.api_ids)
    return Success(msg="角色权限更新成功")


# ==================== 部门管理 ====================


@system_router.get("/departments", summary="获取部门列表")
async def list_departments(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="部门名搜索"),
):
    """获取部门列表"""
    q = Q()
    if name:
        q &= Q(name__icontains=name)

    total, departments = await department_controller.list(
        page=page, page_size=page_size, search=q
    )

    # 转换为响应格式
    data = []
    for dept in departments:
        users_count = await department_controller.get_users_count(dept.id)
        dept_dict = {
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "parent_id": dept.parent_id,
            "sort_order": dept.sort_order,
            "is_active": dept.is_active,
            "created_at": dept.created_at.isoformat(),
            "updated_at": dept.updated_at.isoformat(),
            "users_count": users_count,
        }
        data.append(dept_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@system_router.get("/departments/tree", summary="获取部门树形结构")
async def get_departments_tree():
    """获取部门树形结构"""
    departments = await department_controller.list_tree()

    async def build_tree(dept):
        users_count = await department_controller.get_users_count(dept.id)
        children = getattr(dept, "_children", [])

        return {
            "id": dept.id,
            "name": dept.name,
            "description": dept.description,
            "parent_id": dept.parent_id,
            "sort_order": dept.sort_order,
            "is_active": dept.is_active,
            "created_at": dept.created_at.isoformat(),
            "updated_at": dept.updated_at.isoformat(),
            "users_count": users_count,
            "children": [await build_tree(child) for child in children],
        }

    data = [await build_tree(dept) for dept in departments]
    return Success(data=data)


@system_router.get("/departments/{dept_id}", summary="获取部门详情")
async def get_department(dept_id: int):
    """获取部门详情"""
    dept = await department_controller.get(id=dept_id)
    users_count = await department_controller.get_users_count(dept.id)

    dept_dict = {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
        "parent_id": dept.parent_id,
        "sort_order": dept.sort_order,
        "is_active": dept.is_active,
        "created_at": dept.created_at.isoformat(),
        "updated_at": dept.updated_at.isoformat(),
        "users_count": users_count,
    }

    return Success(data=dept_dict)


@system_router.post("/departments", summary="创建部门")
async def create_department(dept_in: DepartmentCreate):
    """创建部门"""
    await department_controller.create(obj_in=dept_in)
    return Success(msg="部门创建成功")


@system_router.put("/departments/{dept_id}", summary="更新部门")
async def update_department(dept_id: int, dept_in: DepartmentUpdate):
    """更新部门"""
    dept_in.id = dept_id
    await department_controller.update(id=dept_id, obj_in=dept_in)
    return Success(msg="部门更新成功")


@system_router.delete("/departments/{dept_id}", summary="删除部门")
async def delete_department(dept_id: int):
    """删除部门"""
    # 检查是否有子部门
    children = await department_controller.get_children(dept_id)
    if children:
        raise HTTPException(status_code=400, detail="存在子部门，无法删除")

    # 检查是否有用户
    users_count = await department_controller.get_users_count(dept_id)
    if users_count > 0:
        raise HTTPException(status_code=400, detail="部门下有用户，无法删除")

    await department_controller.remove(id=dept_id)
    return Success(msg="部门删除成功")


# ==================== API管理 ====================


@system_router.get("/apis", summary="获取API列表")
async def list_apis(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    path: str = Query("", description="API路径搜索"),
    method: str = Query("", description="请求方法"),
    tags: str = Query("", description="标签搜索"),
):
    """获取API列表"""
    q = Q()
    if path:
        q &= Q(path__icontains=path)
    if method:
        q &= Q(method=method)
    if tags:
        q &= Q(tags__icontains=tags)

    total, apis = await api_controller.list(page=page, page_size=page_size, search=q)

    # 转换为响应格式
    data = []
    for api in apis:
        api_dict = {
            "id": api.id,
            "path": api.path,
            "method": api.method,
            "summary": api.summary,
            "description": api.description,
            "tags": api.tags,
            "is_active": api.is_active,
            "created_at": api.created_at.isoformat(),
            "updated_at": api.updated_at.isoformat(),
        }
        data.append(api_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@system_router.get("/apis/{api_id}", summary="获取API详情")
async def get_api(api_id: int):
    """获取API详情"""
    api = await api_controller.get(id=api_id)

    api_dict = {
        "id": api.id,
        "path": api.path,
        "method": api.method,
        "summary": api.summary,
        "description": api.description,
        "tags": api.tags,
        "is_active": api.is_active,
        "created_at": api.created_at.isoformat(),
        "updated_at": api.updated_at.isoformat(),
    }

    return Success(data=api_dict)


@system_router.post("/apis", summary="创建API")
async def create_api(api_in: ApiCreate):
    """创建API"""
    # 检查API是否已存在
    if await api_controller.is_exist(api_in.path, api_in.method):
        raise HTTPException(status_code=400, detail="API已存在")

    await api_controller.create(obj_in=api_in)
    return Success(msg="API创建成功")


@system_router.put("/apis/{api_id}", summary="更新API")
async def update_api(api_id: int, api_in: ApiUpdate):
    """更新API"""
    api_in.id = api_id
    await api_controller.update(id=api_id, obj_in=api_in)
    return Success(msg="API更新成功")


@system_router.delete("/apis/{api_id}", summary="删除API")
async def delete_api(api_id: int):
    """删除API"""
    await api_controller.remove(id=api_id)
    return Success(msg="API删除成功")


@system_router.post("/apis/sync", summary="同步API列表")
async def sync_apis(request: Request):
    """从FastAPI应用同步API列表"""
    try:
        # 获取FastAPI应用实例
        app = request.app

        # 同步API
        result = await permission_service.sync_apis_from_app(app)

        # 初始化默认权限
        await permission_service.init_default_permissions()

        return Success(
            data=result,
            msg=f"API同步成功，新增 {result['synced_count']} 个，更新 {result['updated_count']} 个",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"API同步失败: {str(e)}")
