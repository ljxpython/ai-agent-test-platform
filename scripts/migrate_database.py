#!/usr/bin/env python3
"""
数据库迁移脚本
支持从SQLite迁移到MySQL，以及数据库类型切换
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger
from tortoise import Tortoise

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.conf.config import settings


class DatabaseMigrator:
    """数据库迁移器"""

    def __init__(self):
        self.source_config = None
        self.target_config = None

    async def migrate_sqlite_to_mysql(self):
        """从SQLite迁移到MySQL"""
        logger.info("🚀 开始从SQLite迁移到MySQL...")

        # 构建SQLite配置
        sqlite_path = project_root / "backend" / "data" / "aitestlab.db"
        sqlite_url = f"sqlite://{sqlite_path}"

        # 构建MySQL配置
        mysql_config = getattr(settings, "database", {}).get("mysql", {})
        mysql_url = self._build_mysql_url(mysql_config)

        logger.info(f"源数据库 (SQLite): {sqlite_url}")
        logger.info(f"目标数据库 (MySQL): {mysql_url}")

        # 检查SQLite数据库是否存在
        if not sqlite_path.exists():
            logger.error(f"SQLite数据库文件不存在: {sqlite_path}")
            return False

        try:
            # 导出SQLite数据
            sqlite_data = await self._export_sqlite_data(sqlite_url)
            logger.info(f"✅ SQLite数据导出完成，共 {len(sqlite_data)} 个表")

            # 导入到MySQL
            await self._import_mysql_data(mysql_url, sqlite_data)
            logger.success("✅ 数据迁移到MySQL完成")

            return True

        except Exception as e:
            logger.error(f"❌ 数据库迁移失败: {e}")
            return False

    def _build_mysql_url(self, mysql_config: Dict[str, Any]) -> str:
        """构建MySQL连接URL"""
        host = mysql_config.get("host", "localhost")
        port = mysql_config.get("port", 3306)
        user = mysql_config.get("user", "root")
        password = mysql_config.get("password", "")
        database = mysql_config.get("database", "aitestlab")
        charset = mysql_config.get("charset", "utf8mb4")

        return f"mysql://{user}:{password}@{host}:{port}/{database}?charset={charset}"

    async def _export_sqlite_data(self, sqlite_url: str) -> Dict[str, List[Dict]]:
        """导出SQLite数据"""
        logger.info("📤 导出SQLite数据...")

        # 配置SQLite连接
        sqlite_config = {
            "connections": {"default": sqlite_url},
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
                        "aerich.models",
                    ],
                    "default_connection": "default",
                },
            },
        }

        await Tortoise.init(config=sqlite_config)

        try:
            data = {}

            # 导出用户相关数据
            from backend.models.department import Department
            from backend.models.role import Role
            from backend.models.user import User

            data["departments"] = [
                await self._serialize_model(dept) for dept in await Department.all()
            ]
            data["roles"] = [
                await self._serialize_model(role) for role in await Role.all()
            ]
            data["users"] = [
                await self._serialize_model(user) for user in await User.all()
            ]

            # 导出项目数据
            from backend.models.project import Project

            data["projects"] = [
                await self._serialize_model(project) for project in await Project.all()
            ]

            # 导出RAG相关数据
            from backend.models.rag import RAGCollection
            from backend.models.rag_file import RAGFile

            data["rag_collections"] = [
                await self._serialize_model(collection)
                for collection in await RAGCollection.all()
            ]
            data["rag_files"] = [
                await self._serialize_model(file) for file in await RAGFile.all()
            ]

            # 导出聊天数据
            from backend.models.chat import ChatMessage, ChatSession

            data["chat_sessions"] = [
                await self._serialize_model(session)
                for session in await ChatSession.all()
            ]
            data["chat_messages"] = [
                await self._serialize_model(message)
                for message in await ChatMessage.all()
            ]

            # 导出测试用例数据
            from backend.models.testcase import TestCase

            data["test_cases"] = [
                await self._serialize_model(case) for case in await TestCase.all()
            ]

            # 导出API权限数据
            from backend.models.api import APIPermission

            data["api_permissions"] = [
                await self._serialize_model(api) for api in await APIPermission.all()
            ]

            logger.info("📊 数据导出统计:")
            for table, records in data.items():
                logger.info(f"  {table}: {len(records)} 条记录")

            return data

        finally:
            await Tortoise.close_connections()

    async def _serialize_model(self, model_instance) -> Dict[str, Any]:
        """序列化模型实例"""
        data = {}
        for field_name in model_instance._meta.fields:
            value = getattr(model_instance, field_name)
            # 处理特殊类型
            if hasattr(value, "isoformat"):  # datetime对象
                data[field_name] = value.isoformat()
            else:
                data[field_name] = value
        return data

    async def _import_mysql_data(self, mysql_url: str, data: Dict[str, List[Dict]]):
        """导入数据到MySQL"""
        logger.info("📥 导入数据到MySQL...")

        # 配置MySQL连接
        mysql_config = {
            "connections": {"default": mysql_url},
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
                        "aerich.models",
                    ],
                    "default_connection": "default",
                },
            },
        }

        await Tortoise.init(config=mysql_config)

        try:
            # 生成数据库表结构
            await Tortoise.generate_schemas()
            logger.info("✅ MySQL表结构创建完成")

            # 按依赖顺序导入数据
            import_order = [
                ("departments", "backend.models.department", "Department"),
                ("roles", "backend.models.role", "Role"),
                ("users", "backend.models.user", "User"),
                ("projects", "backend.models.project", "Project"),
                ("rag_collections", "backend.models.rag", "RAGCollection"),
                ("rag_files", "backend.models.rag_file", "RAGFile"),
                ("chat_sessions", "backend.models.chat", "ChatSession"),
                ("chat_messages", "backend.models.chat", "ChatMessage"),
                ("test_cases", "backend.models.testcase", "TestCase"),
                ("api_permissions", "backend.models.api", "APIPermission"),
            ]

            for table_name, module_path, model_name in import_order:
                if table_name in data and data[table_name]:
                    await self._import_table_data(
                        module_path, model_name, data[table_name]
                    )
                    logger.info(
                        f"✅ {table_name}: {len(data[table_name])} 条记录导入完成"
                    )

        finally:
            await Tortoise.close_connections()

    async def _import_table_data(
        self, module_path: str, model_name: str, records: List[Dict]
    ):
        """导入单个表的数据"""
        if not records:
            return

        # 动态导入模型
        module = __import__(module_path, fromlist=[model_name])
        model_class = getattr(module, model_name)

        # 批量创建记录
        for record in records:
            try:
                # 处理datetime字段
                for key, value in record.items():
                    if isinstance(value, str) and "T" in value and ":" in value:
                        try:
                            from datetime import datetime

                            record[key] = datetime.fromisoformat(
                                value.replace("Z", "+00:00")
                            )
                        except:
                            pass

                await model_class.create(**record)
            except Exception as e:
                logger.warning(f"导入记录失败 {model_name}: {e}")
                continue


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print(
            "  python scripts/migrate_database.py sqlite_to_mysql  # 从SQLite迁移到MySQL"
        )
        return

    command = sys.argv[1]
    migrator = DatabaseMigrator()

    if command == "sqlite_to_mysql":
        success = await migrator.migrate_sqlite_to_mysql()
        if success:
            logger.success("🎉 数据库迁移完成！")
            logger.info("💡 请更新 backend/conf/settings.yaml 中的数据库类型为 'mysql'")
        else:
            logger.error("❌ 数据库迁移失败")
            sys.exit(1)
    else:
        logger.error(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
