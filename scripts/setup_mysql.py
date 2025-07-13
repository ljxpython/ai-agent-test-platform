#!/usr/bin/env python3
"""
MySQL数据库设置脚本
用于创建MySQL数据库和用户
"""

import asyncio
import sys
from pathlib import Path

from loguru import logger

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.conf.config import settings


async def setup_mysql_database():
    """设置MySQL数据库"""
    logger.info("🚀 开始设置MySQL数据库...")

    try:
        # 获取MySQL配置
        mysql_config = getattr(settings, "database", {}).get("mysql", {})

        host = mysql_config.get("host", "localhost")
        port = mysql_config.get("port", 3306)
        root_user = "root"  # 使用root用户创建数据库
        root_password = input("请输入MySQL root密码: ")

        target_user = mysql_config.get("user", "aitestlab")
        target_password = mysql_config.get("password", "")
        target_database = mysql_config.get("database", "aitestlab")

        logger.info(f"🏠 MySQL主机: {host}:{port}")
        logger.info(f"🗄️ 目标数据库: {target_database}")
        logger.info(f"👤 目标用户: {target_user}")

        # 导入MySQL连接库
        try:
            import aiomysql
        except ImportError:
            logger.error("❌ 请先安装aiomysql: poetry add aiomysql")
            return False

        # 连接到MySQL服务器
        connection = await aiomysql.connect(
            host=host,
            port=port,
            user=root_user,
            password=root_password,
            charset="utf8mb4",
        )

        try:
            cursor = await connection.cursor()

            # 创建数据库
            logger.info(f"📝 创建数据库: {target_database}")
            await cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{target_database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )

            # 创建用户（如果不存在）
            logger.info(f"👤 创建用户: {target_user}")
            await cursor.execute(
                f"CREATE USER IF NOT EXISTS '{target_user}'@'%' IDENTIFIED BY '{target_password}'"
            )

            # 授予权限
            logger.info(f"🔑 授予权限...")
            await cursor.execute(
                f"GRANT ALL PRIVILEGES ON `{target_database}`.* TO '{target_user}'@'%'"
            )
            await cursor.execute("FLUSH PRIVILEGES")

            await connection.commit()
            logger.success("✅ MySQL数据库设置完成")

            # 测试连接
            logger.info("🔍 测试新用户连接...")
            test_connection = await aiomysql.connect(
                host=host,
                port=port,
                user=target_user,
                password=target_password,
                db=target_database,
                charset="utf8mb4",
            )

            test_cursor = await test_connection.cursor()
            await test_cursor.execute("SELECT 1")
            result = await test_cursor.fetchone()

            await test_connection.close()

            if result:
                logger.success("✅ 用户连接测试成功")
                return True
            else:
                logger.error("❌ 用户连接测试失败")
                return False

        finally:
            await connection.close()

    except Exception as e:
        logger.error(f"❌ MySQL数据库设置失败: {e}")
        return False


async def check_mysql_connection():
    """检查MySQL连接"""
    logger.info("🔍 检查MySQL连接...")

    try:
        mysql_config = getattr(settings, "database", {}).get("mysql", {})

        host = mysql_config.get("host", "localhost")
        port = mysql_config.get("port", 3306)
        user = mysql_config.get("user", "aitestlab")
        password = mysql_config.get("password", "")
        database = mysql_config.get("database", "aitestlab")

        import aiomysql

        connection = await aiomysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            charset="utf8mb4",
        )

        cursor = await connection.cursor()
        await cursor.execute("SELECT VERSION()")
        version = await cursor.fetchone()

        await connection.close()

        logger.success(f"✅ MySQL连接成功 - 版本: {version[0]}")
        return True

    except Exception as e:
        logger.error(f"❌ MySQL连接失败: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/setup_mysql.py setup    # 设置MySQL数据库")
        print("  python scripts/setup_mysql.py check    # 检查MySQL连接")
        return

    command = sys.argv[1]

    if command == "setup":
        success = asyncio.run(setup_mysql_database())
        if success:
            logger.success("🎉 MySQL数据库设置完成！")
            logger.info("💡 现在可以使用 'make switch-to-mysql' 切换到MySQL数据库")
        else:
            logger.error("❌ MySQL数据库设置失败")
            sys.exit(1)
    elif command == "check":
        success = asyncio.run(check_mysql_connection())
        if success:
            logger.success("🎉 MySQL连接正常")
        else:
            logger.error("❌ MySQL连接失败")
            sys.exit(1)
    else:
        logger.error(f"未知命令: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
