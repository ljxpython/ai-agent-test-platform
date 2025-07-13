import os
from pathlib import Path

from fastapi import FastAPI
from loguru import logger
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from backend.conf.config import settings
from backend.conf.constants import backend_path


def get_database_url() -> str:
    """根据配置动态生成数据库URL"""
    db_config = getattr(settings, "database", {})
    db_type = db_config.get("type", "sqlite")

    if db_type == "sqlite":
        sqlite_config = db_config.get("sqlite", {})
        db_path = sqlite_config.get("path", "./data/aitestlab.db")

        # 确保路径是绝对路径
        if not Path(db_path).is_absolute():
            db_path = backend_path / db_path.lstrip("./")

        # 确保数据目录存在
        data_dir = Path(db_path).parent
        if not data_dir.exists():
            data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"创建数据目录: {data_dir}")

        return f"sqlite://{db_path}"

    elif db_type == "mysql":
        mysql_config = db_config.get("mysql", {})
        host = mysql_config.get("host", "localhost")
        port = mysql_config.get("port", 3306)
        user = mysql_config.get("user", "root")
        password = mysql_config.get("password", "")
        database = mysql_config.get("database", "aitestlab")
        charset = mysql_config.get("charset", "utf8mb4")

        return f"mysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"

    else:
        raise ValueError(f"不支持的数据库类型: {db_type}")


# 动态获取数据库URL
DATABASE_URL = get_database_url()

# Tortoise ORM 配置
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "backend.models.user",
                "backend.models.chat",
                "backend.models.testcase",
                "backend.models.midscene",
                "backend.models.role",
                "backend.models.department",
                "backend.models.api",
                "backend.models.rag",
                "backend.models.rag_file",
                "backend.models.project",
                "backend.models.ui_task",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}


async def init_db():
    """初始化数据库"""
    try:
        # 获取数据库配置信息
        db_config = getattr(settings, "database", {})
        db_type = db_config.get("type", "sqlite")

        logger.info(f"🗄️ 初始化数据库 - 类型: {db_type}")
        logger.info(f"🔗 数据库连接: {DATABASE_URL}")

        # 初始化 Tortoise ORM
        await Tortoise.init(config=TORTOISE_ORM)
        logger.info("Tortoise ORM 初始化成功")

        # 生成数据库表
        await Tortoise.generate_schemas()
        logger.info("数据库表生成成功")

        # 创建默认用户
        await create_default_user()

        # 初始化默认项目
        await init_default_project()

        # 初始化默认RAG Collections
        await init_default_rag_collections()

        logger.success(f"🚀 数据库初始化完成 - {db_type.upper()}")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


async def init_data(app=None):
    """初始化应用数据 - 从init_app.py迁移过来"""
    logger.info("开始初始化应用数据...")

    try:
        # 初始化数据库
        logger.debug("初始化数据库连接...")
        await init_db()

        # 创建默认用户
        logger.debug("创建默认用户...")
        await create_default_user()

        # 如果提供了app实例，同步API权限
        if app:
            try:
                from backend.services.auth.permission_service import permission_service

                logger.info("开始同步API权限...")
                result = await permission_service.sync_apis_from_app(app)
                logger.info(
                    f"API权限同步完成: 新增 {result['synced_count']} 个，更新 {result['updated_count']} 个"
                )

                # 初始化默认权限
                await permission_service.init_default_permissions()
                logger.info("默认权限初始化完成")
            except Exception as e:
                logger.warning(f"API权限同步失败，将在运行时手动同步: {e}")

        logger.success("🚀 应用数据初始化完成")
    except Exception as e:
        logger.error(f"应用数据初始化失败: {e}")
        raise


async def create_default_user():
    """创建默认用户"""
    try:
        from backend.models.department import Department
        from backend.models.role import Role
        from backend.models.user import User
        from backend.utils.password import hash_password

        # 检查是否已存在默认用户
        existing_user = await User.get_or_none(username="test")
        if existing_user:
            logger.info("默认用户已存在")
            return

        # 创建默认部门
        default_dept = await Department.get_or_none(name="AI测试部")
        if not default_dept:
            default_dept = await Department.create(
                name="AI测试部",
                description="AI测试实验室默认部门",
                sort_order=0,
                is_active=True,
            )
            logger.info("默认部门创建成功: AI测试部")

        # 创建默认角色
        admin_role = await Role.get_or_none(name="管理员")
        if not admin_role:
            admin_role = await Role.create(
                name="管理员", description="系统管理员角色", is_active=True
            )
            logger.info("默认角色创建成功: 管理员")

        # 创建默认用户
        default_user = await User.create(
            username="test",
            email="test@example.com",
            full_name="测试用户",
            password_hash=hash_password("test"),
            is_active=True,
            is_superuser=True,
            dept=default_dept,
        )

        # 分配角色
        await default_user.roles.add(admin_role)

        logger.success("默认用户创建成功:")
        logger.info("  用户名: test")
        logger.info("  密码: test")
        logger.info("  邮箱: test@example.com")
        logger.info("  部门: AI测试部")
        logger.info("  角色: 管理员")

    except Exception as e:
        logger.error(f"创建默认用户失败: {e}")
        raise


async def init_default_rag_collections():
    """初始化默认RAG Collections"""
    try:
        from backend.services.rag.collection_service import collection_service

        logger.info("🚀 开始初始化默认RAG Collections...")
        created_count = await collection_service.initialize_default_collections()

        if created_count > 0:
            logger.success(
                f"✅ 默认RAG Collections初始化完成，新创建 {created_count} 个"
            )
        else:
            logger.info("ℹ️ 默认RAG Collections已存在，无需创建")

    except Exception as e:
        logger.error(f"❌ 初始化默认RAG Collections失败: {e}")
        # 不抛出异常，避免影响整个数据库初始化过程


async def init_default_project():
    """初始化默认项目"""
    try:
        from backend.models.project import Project

        logger.info("🚀 开始初始化默认项目...")

        # 检查是否已存在默认项目
        existing_default = await Project.get_or_none(is_default=True)
        if existing_default:
            logger.info("ℹ️ 默认项目已存在，无需创建")
            return

        # 创建默认项目
        default_project = await Project.create(
            name="general",
            display_name="通用项目",
            description="系统默认项目，用于存放通用的测试用例、RAG知识库等数据",
            is_default=True,
            is_active=True,
            settings={
                "auto_created": True,
                "system_project": True,
            },
        )

        logger.success(f"✅ 默认项目创建成功: {default_project.display_name}")

    except Exception as e:
        logger.error(f"❌ 初始化默认项目失败: {e}")
        # 不抛出异常，避免影响整个数据库初始化过程


async def close_db():
    """关闭数据库连接"""
    try:
        await Tortoise.close_connections()
        logger.info("数据库连接已关闭")
    except Exception as e:
        logger.error(f"关闭数据库连接失败: {e}")


def setup_database(app: FastAPI):
    """设置数据库"""
    register_tortoise(
        app,
        config=TORTOISE_ORM,
        generate_schemas=True,
        add_exception_handlers=True,
    )
