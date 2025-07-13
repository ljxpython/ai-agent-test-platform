#!/usr/bin/env python3
"""
数据库切换脚本
支持在SQLite和MySQL之间动态切换数据库配置
"""

import sys
from pathlib import Path

import yaml
from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DatabaseSwitcher:
    """数据库切换器"""

    def __init__(self):
        self.settings_file = project_root / "backend" / "conf" / "settings.yaml"

    def switch_to_sqlite(self):
        """切换到SQLite数据库"""
        logger.info("🔄 切换到SQLite数据库...")

        try:
            # 读取配置文件
            with open(self.settings_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新数据库配置
            if "test" not in config:
                config["test"] = {}
            if "database" not in config["test"]:
                config["test"]["database"] = {}

            config["test"]["database"]["type"] = "sqlite"

            # 写回配置文件
            with open(self.settings_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    config, f, default_flow_style=False, allow_unicode=True, indent=2
                )

            logger.success("✅ 已切换到SQLite数据库")
            logger.info("📁 数据库文件: ./backend/data/aitestlab.db")

        except Exception as e:
            logger.error(f"❌ 切换到SQLite失败: {e}")
            return False

        return True

    def switch_to_mysql(self):
        """切换到MySQL数据库"""
        logger.info("🔄 切换到MySQL数据库...")

        try:
            # 读取配置文件
            with open(self.settings_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # 更新数据库配置
            if "test" not in config:
                config["test"] = {}
            if "database" not in config["test"]:
                config["test"]["database"] = {}

            config["test"]["database"]["type"] = "mysql"

            # 写回配置文件
            with open(self.settings_file, "w", encoding="utf-8") as f:
                yaml.dump(
                    config, f, default_flow_style=False, allow_unicode=True, indent=2
                )

            logger.success("✅ 已切换到MySQL数据库")

            # 显示MySQL配置信息
            mysql_config = config["test"]["database"].get("mysql", {})
            logger.info(f"🏠 主机: {mysql_config.get('host', 'localhost')}")
            logger.info(f"🔌 端口: {mysql_config.get('port', 3306)}")
            logger.info(f"👤 用户: {mysql_config.get('user', 'root')}")
            logger.info(f"🗄️ 数据库: {mysql_config.get('database', 'aitestlab')}")

        except Exception as e:
            logger.error(f"❌ 切换到MySQL失败: {e}")
            return False

        return True

    def show_current_config(self):
        """显示当前数据库配置"""
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            db_config = config.get("test", {}).get("database", {})
            db_type = db_config.get("type", "sqlite")

            logger.info("📊 当前数据库配置:")
            logger.info(f"🔧 类型: {db_type.upper()}")

            if db_type == "sqlite":
                sqlite_config = db_config.get("sqlite", {})
                logger.info(
                    f"📁 路径: {sqlite_config.get('path', './data/aitestlab.db')}"
                )
            elif db_type == "mysql":
                mysql_config = db_config.get("mysql", {})
                logger.info(f"🏠 主机: {mysql_config.get('host', 'localhost')}")
                logger.info(f"🔌 端口: {mysql_config.get('port', 3306)}")
                logger.info(f"👤 用户: {mysql_config.get('user', 'root')}")
                logger.info(f"🗄️ 数据库: {mysql_config.get('database', 'aitestlab')}")

        except Exception as e:
            logger.error(f"❌ 读取配置失败: {e}")

    def test_connection(self):
        """测试数据库连接"""
        logger.info("🔍 测试数据库连接...")

        try:
            # 导入数据库模块
            import asyncio

            from tortoise import Tortoise

            from backend.api_core.database import TORTOISE_ORM, get_database_url

            async def test_db():
                try:
                    db_url = get_database_url()
                    logger.info(f"🔗 连接URL: {db_url}")

                    await Tortoise.init(config=TORTOISE_ORM)
                    logger.success("✅ 数据库连接成功")

                    # 测试查询
                    connection = Tortoise.get_connection("default")
                    result = await connection.execute_query("SELECT 1 as test")
                    logger.info(f"🧪 测试查询结果: {result}")

                    await Tortoise.close_connections()
                    return True

                except Exception as e:
                    logger.error(f"❌ 数据库连接失败: {e}")
                    return False

            return asyncio.run(test_db())

        except Exception as e:
            logger.error(f"❌ 连接测试异常: {e}")
            return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/switch_database.py sqlite     # 切换到SQLite")
        print("  python scripts/switch_database.py mysql      # 切换到MySQL")
        print("  python scripts/switch_database.py status     # 显示当前配置")
        print("  python scripts/switch_database.py test       # 测试数据库连接")
        return

    command = sys.argv[1]
    switcher = DatabaseSwitcher()

    if command == "sqlite":
        success = switcher.switch_to_sqlite()
        if success:
            logger.info("💡 请重启应用以使配置生效")
    elif command == "mysql":
        success = switcher.switch_to_mysql()
        if success:
            logger.info("💡 请重启应用以使配置生效")
    elif command == "status":
        switcher.show_current_config()
    elif command == "test":
        success = switcher.test_connection()
        if success:
            logger.success("🎉 数据库连接测试通过")
        else:
            logger.error("❌ 数据库连接测试失败")
    else:
        logger.error(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
