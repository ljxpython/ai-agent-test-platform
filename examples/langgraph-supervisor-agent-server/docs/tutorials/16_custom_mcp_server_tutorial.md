# 16. 自定义 MCP 服务器教学

## 🎯 学习目标

通过这个教程，你将学会：
- 如何创建自定义 MCP 服务器
- MCP 服务器的架构和协议实现
- 工具注册和资源管理
- 服务器部署和维护最佳实践

## 📚 核心概念

### 1. 什么是 MCP 服务器？

MCP 服务器是**实现 MCP 协议的后端服务**，为 AI 应用提供特定功能的工具：

```
AI 应用 ← MCP 客户端 ← MCP 协议 → MCP 服务器 → 业务逻辑/外部服务
```

**MCP 服务器的职责：**
- **工具注册**：向客户端暴露可用工具
- **请求处理**：执行工具调用并返回结果
- **资源管理**：管理连接、状态和资源
- **错误处理**：处理异常和错误情况

### 2. 服务器架构

```
┌─────────────────────────────────────┐
│           MCP 服务器                │
├─────────────────────────────────────┤
│  协议层 (Protocol Handler)          │
│  ├── 消息解析                      │
│  ├── 工具路由                      │
│  └── 响应序列化                    │
├─────────────────────────────────────┤
│  业务层 (Business Logic)           │
│  ├── 工具实现                      │
│  ├── 数据验证                      │
│  └── 权限检查                      │
├─────────────────────────────────────┤
│  数据层 (Data Access)              │
│  ├── 数据库连接                    │
│  ├── 文件系统                      │
│  └── 外部 API                      │
└─────────────────────────────────────┘
```

### 3. 工具定义

```python
from mcp.types import Tool, TextContent

# 定义工具
calculator_tool = Tool(
    name="calculate",
    description="执行数学计算",
    inputSchema={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式"
            }
        },
        "required": ["expression"]
    }
)
```

## 🔍 代码详细解析

### 基础 MCP 服务器

```python
import asyncio
import json
import sys
from typing import Any, Sequence
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult
)

class CustomMCPServer:
    """自定义 MCP 服务器"""

    def __init__(self, name: str = "custom-mcp-server"):
        self.server = Server(name)
        self.tools = {}
        self._setup_handlers()

    def _setup_handlers(self):
        """设置处理器"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """列出可用工具"""
            return list(self.tools.values())

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """调用工具"""
            if name not in self.tools:
                raise ValueError(f"未知工具: {name}")

            # 获取工具处理器
            handler = getattr(self, f"_handle_{name}", None)
            if not handler:
                raise ValueError(f"工具 {name} 没有处理器")

            try:
                # 验证参数
                self._validate_arguments(name, arguments)

                # 执行工具
                result = await handler(arguments)

                # 返回结果
                return [TextContent(type="text", text=str(result))]

            except Exception as e:
                error_msg = f"工具执行失败: {e}"
                return [TextContent(type="text", text=error_msg)]

    def register_tool(self, tool: Tool):
        """注册工具"""
        self.tools[tool.name] = tool
        print(f"注册工具: {tool.name}")

    def _validate_arguments(self, tool_name: str, arguments: dict):
        """验证参数"""
        tool = self.tools[tool_name]
        schema = tool.inputSchema

        # 简单的参数验证
        if "required" in schema:
            for required_field in schema["required"]:
                if required_field not in arguments:
                    raise ValueError(f"缺少必需参数: {required_field}")

    async def run(self):
        """运行服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

# 创建服务器实例
mcp_server = CustomMCPServer("demo-server")
```

### 计算器工具实现

```python
import ast
import operator

class CalculatorMCPServer(CustomMCPServer):
    """计算器 MCP 服务器"""

    def __init__(self):
        super().__init__("calculator-server")
        self._register_calculator_tools()

    def _register_calculator_tools(self):
        """注册计算器工具"""

        # 基础计算工具
        calculate_tool = Tool(
            name="calculate",
            description="执行基础数学计算（支持 +, -, *, /, **, (), 数字）",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2 + 3 * 4'"
                    }
                },
                "required": ["expression"]
            }
        )

        # 统计计算工具
        statistics_tool = Tool(
            name="statistics",
            description="计算数字列表的统计信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "numbers": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "数字列表"
                    },
                    "operations": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["mean", "median", "mode", "std", "min", "max", "sum"]
                        },
                        "description": "要计算的统计操作"
                    }
                },
                "required": ["numbers", "operations"]
            }
        )

        self.register_tool(calculate_tool)
        self.register_tool(statistics_tool)

    async def _handle_calculate(self, arguments: dict) -> str:
        """处理计算请求"""
        expression = arguments["expression"]

        try:
            # 安全的数学表达式求值
            result = self._safe_eval(expression)
            return f"计算结果: {expression} = {result}"
        except Exception as e:
            return f"计算错误: {e}"

    async def _handle_statistics(self, arguments: dict) -> str:
        """处理统计计算请求"""
        numbers = arguments["numbers"]
        operations = arguments["operations"]

        if not numbers:
            return "错误: 数字列表不能为空"

        results = {}

        try:
            for op in operations:
                if op == "mean":
                    results[op] = sum(numbers) / len(numbers)
                elif op == "median":
                    sorted_nums = sorted(numbers)
                    n = len(sorted_nums)
                    if n % 2 == 0:
                        results[op] = (sorted_nums[n//2-1] + sorted_nums[n//2]) / 2
                    else:
                        results[op] = sorted_nums[n//2]
                elif op == "min":
                    results[op] = min(numbers)
                elif op == "max":
                    results[op] = max(numbers)
                elif op == "sum":
                    results[op] = sum(numbers)
                elif op == "std":
                    mean = sum(numbers) / len(numbers)
                    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
                    results[op] = variance ** 0.5

            # 格式化结果
            result_lines = [f"统计结果 (数据: {numbers}):"]
            for op, value in results.items():
                result_lines.append(f"  {op}: {value:.4f}")

            return "\n".join(result_lines)

        except Exception as e:
            return f"统计计算错误: {e}"

    def _safe_eval(self, expression: str) -> float:
        """安全的表达式求值"""
        # 定义允许的操作
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def eval_node(node):
            if isinstance(node, ast.Constant):  # 数字
                return node.value
            elif isinstance(node, ast.BinOp):  # 二元操作
                left = eval_node(node.left)
                right = eval_node(node.right)
                op = allowed_operators.get(type(node.op))
                if op is None:
                    raise ValueError(f"不支持的操作: {type(node.op).__name__}")
                return op(left, right)
            elif isinstance(node, ast.UnaryOp):  # 一元操作
                operand = eval_node(node.operand)
                op = allowed_operators.get(type(node.op))
                if op is None:
                    raise ValueError(f"不支持的操作: {type(node.op).__name__}")
                return op(operand)
            else:
                raise ValueError(f"不支持的节点类型: {type(node).__name__}")

        try:
            # 解析表达式
            tree = ast.parse(expression, mode='eval')

            # 求值
            result = eval_node(tree.body)

            return result

        except SyntaxError:
            raise ValueError("无效的数学表达式")
        except ZeroDivisionError:
            raise ValueError("除零错误")
        except Exception as e:
            raise ValueError(f"表达式求值失败: {e}")

# 创建计算器服务器
calculator_server = CalculatorMCPServer()
```

### 文件系统工具服务器

```python
import os
import json
from pathlib import Path

class FileSystemMCPServer(CustomMCPServer):
    """文件系统 MCP 服务器"""

    def __init__(self, base_path: str = "."):
        super().__init__("filesystem-server")
        self.base_path = Path(base_path).resolve()
        self.allowed_extensions = {'.txt', '.md', '.json', '.csv', '.log', '.py'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self._register_filesystem_tools()

    def _register_filesystem_tools(self):
        """注册文件系统工具"""

        # 读取文件工具
        read_file_tool = Tool(
            name="read_file",
            description="读取文件内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径（相对于基础目录）"
                    }
                },
                "required": ["path"]
            }
        )

        # 写入文件工具
        write_file_tool = Tool(
            name="write_file",
            description="写入文件内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "文件路径"
                    },
                    "content": {
                        "type": "string",
                        "description": "文件内容"
                    }
                },
                "required": ["path", "content"]
            }
        )

        # 列出目录工具
        list_directory_tool = Tool(
            name="list_directory",
            description="列出目录内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径",
                        "default": "."
                    }
                }
            }
        )

        # 创建目录工具
        create_directory_tool = Tool(
            name="create_directory",
            description="创建目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "目录路径"
                    }
                },
                "required": ["path"]
            }
        )

        self.register_tool(read_file_tool)
        self.register_tool(write_file_tool)
        self.register_tool(list_directory_tool)
        self.register_tool(create_directory_tool)

    def _resolve_path(self, path: str) -> Path:
        """解析和验证路径"""
        # 防止路径遍历攻击
        if ".." in path or path.startswith("/"):
            raise ValueError("不安全的路径")

        resolved_path = (self.base_path / path).resolve()

        # 确保路径在基础目录内
        if not str(resolved_path).startswith(str(self.base_path)):
            raise ValueError("路径超出允许范围")

        return resolved_path

    def _check_file_extension(self, path: Path):
        """检查文件扩展名"""
        if path.suffix.lower() not in self.allowed_extensions:
            raise ValueError(f"不支持的文件类型: {path.suffix}")

    async def _handle_read_file(self, arguments: dict) -> str:
        """处理读取文件请求"""
        try:
            file_path = self._resolve_path(arguments["path"])

            if not file_path.exists():
                return f"错误: 文件不存在: {arguments['path']}"

            if not file_path.is_file():
                return f"错误: 不是文件: {arguments['path']}"

            # 检查文件大小
            if file_path.stat().st_size > self.max_file_size:
                return f"错误: 文件太大 (最大 {self.max_file_size} 字节)"

            # 检查扩展名
            self._check_file_extension(file_path)

            # 读取文件
            content = file_path.read_text(encoding='utf-8')

            return f"文件内容 ({arguments['path']}):\n{content}"

        except Exception as e:
            return f"读取文件失败: {e}"

    async def _handle_write_file(self, arguments: dict) -> str:
        """处理写入文件请求"""
        try:
            file_path = self._resolve_path(arguments["path"])
            content = arguments["content"]

            # 检查内容大小
            if len(content.encode('utf-8')) > self.max_file_size:
                return f"错误: 内容太大"

            # 检查扩展名
            self._check_file_extension(file_path)

            # 创建父目录
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            file_path.write_text(content, encoding='utf-8')

            return f"文件已写入: {arguments['path']} ({len(content)} 字符)"

        except Exception as e:
            return f"写入文件失败: {e}"

    async def _handle_list_directory(self, arguments: dict) -> str:
        """处理列出目录请求"""
        try:
            dir_path = self._resolve_path(arguments.get("path", "."))

            if not dir_path.exists():
                return f"错误: 目录不存在: {arguments.get('path', '.')}"

            if not dir_path.is_dir():
                return f"错误: 不是目录: {arguments.get('path', '.')}"

            # 列出目录内容
            items = []
            for item in sorted(dir_path.iterdir()):
                item_type = "目录" if item.is_dir() else "文件"
                size = ""
                if item.is_file():
                    size = f" ({item.stat().st_size} 字节)"

                items.append(f"  {item_type}: {item.name}{size}")

            if not items:
                return f"目录为空: {arguments.get('path', '.')}"

            return f"目录内容 ({arguments.get('path', '.')}):\n" + "\n".join(items)

        except Exception as e:
            return f"列出目录失败: {e}"

    async def _handle_create_directory(self, arguments: dict) -> str:
        """处理创建目录请求"""
        try:
            dir_path = self._resolve_path(arguments["path"])

            if dir_path.exists():
                return f"目录已存在: {arguments['path']}"

            # 创建目录
            dir_path.mkdir(parents=True, exist_ok=True)

            return f"目录已创建: {arguments['path']}"

        except Exception as e:
            return f"创建目录失败: {e}"

# 创建文件系统服务器
filesystem_server = FileSystemMCPServer()
```

### 数据库工具服务器

```python
import sqlite3
import json
from typing import List, Dict, Any

class DatabaseMCPServer(CustomMCPServer):
    """数据库 MCP 服务器"""

    def __init__(self, db_path: str = ":memory:"):
        super().__init__("database-server")
        self.db_path = db_path
        self.connection = None
        self._register_database_tools()
        self._init_database()

    def _register_database_tools(self):
        """注册数据库工具"""

        # 查询工具
        query_tool = Tool(
            name="query",
            description="执行 SQL 查询",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "SQL 查询语句"
                    },
                    "params": {
                        "type": "array",
                        "description": "查询参数",
                        "default": []
                    }
                },
                "required": ["sql"]
            }
        )

        # 插入数据工具
        insert_tool = Tool(
            name="insert",
            description="插入数据到表",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {
                        "type": "string",
                        "description": "表名"
                    },
                    "data": {
                        "type": "object",
                        "description": "要插入的数据（字段名: 值）"
                    }
                },
                "required": ["table", "data"]
            }
        )

        # 列出表工具
        list_tables_tool = Tool(
            name="list_tables",
            description="列出数据库中的所有表",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )

        self.register_tool(query_tool)
        self.register_tool(insert_tool)
        self.register_tool(list_tables_tool)

    def _init_database(self):
        """初始化数据库"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # 返回字典格式的行

            # 创建示例表
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    price REAL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 插入示例数据
            self.connection.execute(
                "INSERT OR IGNORE INTO users (name, email) VALUES (?, ?)",
                ("张三", "zhangsan@example.com")
            )

            self.connection.execute(
                "INSERT OR IGNORE INTO products (name, price, category) VALUES (?, ?, ?)",
                ("笔记本电脑", 5999.99, "电子产品")
            )

            self.connection.commit()

        except Exception as e:
            print(f"数据库初始化失败: {e}")

    def _is_safe_query(self, sql: str) -> bool:
        """检查 SQL 查询是否安全"""
        sql_lower = sql.lower().strip()

        # 只允许 SELECT 查询
        if not sql_lower.startswith("select"):
            return False

        # 禁止的关键字
        forbidden_keywords = [
            "drop", "delete", "update", "insert", "alter",
            "create", "truncate", "exec", "execute"
        ]

        for keyword in forbidden_keywords:
            if keyword in sql_lower:
                return False

        return True

    async def _handle_query(self, arguments: dict) -> str:
        """处理查询请求"""
        try:
            sql = arguments["sql"]
            params = arguments.get("params", [])

            # 安全检查
            if not self._is_safe_query(sql):
                return "错误: 只允许 SELECT 查询"

            # 执行查询
            cursor = self.connection.execute(sql, params)
            rows = cursor.fetchall()

            if not rows:
                return "查询结果: 无数据"

            # 格式化结果
            columns = [description[0] for description in cursor.description]
            results = []

            for row in rows:
                row_dict = dict(zip(columns, row))
                results.append(row_dict)

            return f"查询结果 ({len(results)} 行):\n{json.dumps(results, ensure_ascii=False, indent=2)}"

        except Exception as e:
            return f"查询失败: {e}"

    async def _handle_insert(self, arguments: dict) -> str:
        """处理插入请求"""
        try:
            table = arguments["table"]
            data = arguments["data"]

            # 验证表名
            if not table.isalnum() and "_" not in table:
                return "错误: 无效的表名"

            # 构建插入语句
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join(["?" for _ in columns])

            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

            # 执行插入
            cursor = self.connection.execute(sql, values)
            self.connection.commit()

            return f"数据已插入到表 {table}，行ID: {cursor.lastrowid}"

        except Exception as e:
            return f"插入失败: {e}"

    async def _handle_list_tables(self, arguments: dict) -> str:
        """处理列出表请求"""
        try:
            cursor = self.connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )

            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                return "数据库中没有表"

            # 获取每个表的信息
            table_info = []
            for table in tables:
                cursor = self.connection.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_info.append(f"  {table}: {count} 行")

            return f"数据库表 ({len(tables)} 个):\n" + "\n".join(table_info)

        except Exception as e:
            return f"列出表失败: {e}"

    def __del__(self):
        """清理资源"""
        if self.connection:
            self.connection.close()

# 创建数据库服务器
database_server = DatabaseMCPServer()
```

## 🚀 服务器部署和管理

### 1. 服务器启动脚本

```python
#!/usr/bin/env python3
"""
MCP 服务器启动脚本
"""

import sys
import argparse
import asyncio
import logging

def setup_logging(level: str = "INFO"):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mcp_server.log'),
            logging.StreamHandler(sys.stderr)
        ]
    )

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="自定义 MCP 服务器")
    parser.add_argument("--server-type", choices=["calculator", "filesystem", "database"],
                       required=True, help="服务器类型")
    parser.add_argument("--base-path", default=".", help="文件系统基础路径")
    parser.add_argument("--db-path", default=":memory:", help="数据库路径")
    parser.add_argument("--log-level", default="INFO", help="日志级别")

    args = parser.parse_args()

    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # 创建服务器
        if args.server_type == "calculator":
            server = CalculatorMCPServer()
        elif args.server_type == "filesystem":
            server = FileSystemMCPServer(args.base_path)
        elif args.server_type == "database":
            server = DatabaseMCPServer(args.db_path)
        else:
            raise ValueError(f"未知的服务器类型: {args.server_type}")

        logger.info(f"启动 {args.server_type} MCP 服务器...")

        # 运行服务器
        await server.run()

    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 服务器配置管理

```python
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class ServerConfig:
    """服务器配置"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    max_connections: int = 10
    timeout: int = 30
    log_level: str = "INFO"
    security: Dict[str, Any] = None

    def __post_init__(self):
        if self.security is None:
            self.security = {
                "enable_auth": False,
                "allowed_ips": [],
                "rate_limit": 100
            }

class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = "server_config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> ServerConfig:
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return ServerConfig(**data)
            except Exception as e:
                print(f"加载配置失败: {e}")

        # 返回默认配置
        return ServerConfig(name="default-mcp-server")

    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self.save_config()

# 使用配置管理器
config_manager = ConfigManager()
```

### 3. 服务器监控

```python
import time
import psutil
from datetime import datetime
from typing import Dict, List

class ServerMonitor:
    """服务器监控"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.response_times = []
        self.active_connections = 0

    def record_request(self, response_time: float, success: bool = True):
        """记录请求"""
        self.request_count += 1
        self.response_times.append(response_time)

        if not success:
            self.error_count += 1

        # 限制响应时间历史长度
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self.start_time

        # 计算平均响应时间
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)

        # 计算错误率
        error_rate = 0
        if self.request_count > 0:
            error_rate = (self.error_count / self.request_count) * 100

        # 系统资源
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "average_response_time": avg_response_time,
            "active_connections": self.active_connections,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / (1024 * 1024)
            }
        }

    def get_health_status(self) -> str:
        """获取健康状态"""
        stats = self.get_stats()

        # 健康检查规则
        if stats["error_rate_percent"] > 10:
            return "unhealthy"
        elif stats["system"]["cpu_percent"] > 90:
            return "degraded"
        elif stats["system"]["memory_percent"] > 90:
            return "degraded"
        else:
            return "healthy"

    def print_status(self):
        """打印状态"""
        stats = self.get_stats()
        health = self.get_health_status()

        print(f"\n=== MCP 服务器状态 ===")
        print(f"健康状态: {health}")
        print(f"运行时间: {stats['uptime_seconds']:.0f} 秒")
        print(f"总请求数: {stats['total_requests']}")
        print(f"错误率: {stats['error_rate_percent']:.1f}%")
        print(f"平均响应时间: {stats['average_response_time']:.3f} 秒")
        print(f"活跃连接: {stats['active_connections']}")
        print(f"CPU 使用率: {stats['system']['cpu_percent']:.1f}%")
        print(f"内存使用率: {stats['system']['memory_percent']:.1f}%")

# 全局监控实例
server_monitor = ServerMonitor()
```

## 🎯 实践练习

### 练习1：API 集成服务器

```python
import aiohttp
import json

class APIIntegrationServer(CustomMCPServer):
    """API 集成服务器"""

    def __init__(self):
        super().__init__("api-integration-server")
        self.session = None
        self._register_api_tools()

    async def _setup_session(self):
        """设置 HTTP 会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    def _register_api_tools(self):
        """注册 API 工具"""

        weather_tool = Tool(
            name="get_weather",
            description="获取天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                },
                "required": ["city"]
            }
        )

        self.register_tool(weather_tool)

    async def _handle_get_weather(self, arguments: dict) -> str:
        """处理天气查询"""
        await self._setup_session()

        city = arguments["city"]

        try:
            # 模拟天气 API 调用
            # 实际应用中应该调用真实的天气 API
            weather_data = {
                "city": city,
                "temperature": "22°C",
                "condition": "晴天",
                "humidity": "65%",
                "wind": "微风"
            }

            return f"{city} 的天气信息:\n" + json.dumps(weather_data, ensure_ascii=False, indent=2)

        except Exception as e:
            return f"获取天气信息失败: {e}"

    async def cleanup(self):
        """清理资源"""
        if self.session:
            await self.session.close()
```

### 练习2：服务器集群管理

```python
class ServerCluster:
    """服务器集群管理"""

    def __init__(self):
        self.servers = {}
        self.load_balancer = LoadBalancer()

    def register_server(self, server_id: str, server_instance):
        """注册服务器"""
        self.servers[server_id] = {
            "instance": server_instance,
            "status": "active",
            "load": 0,
            "last_health_check": datetime.now()
        }

    async def health_check_all(self):
        """健康检查所有服务器"""
        for server_id, server_info in self.servers.items():
            try:
                # 执行健康检查
                health = await self._check_server_health(server_info["instance"])
                server_info["status"] = "active" if health else "inactive"
                server_info["last_health_check"] = datetime.now()
            except Exception as e:
                print(f"服务器 {server_id} 健康检查失败: {e}")
                server_info["status"] = "error"

    async def _check_server_health(self, server_instance) -> bool:
        """检查单个服务器健康状态"""
        try:
            # 简单的健康检查：尝试列出工具
            tools = await server_instance.server.list_tools()
            return len(tools) > 0
        except:
            return False

    def get_cluster_status(self) -> dict:
        """获取集群状态"""
        total_servers = len(self.servers)
        active_servers = sum(1 for s in self.servers.values() if s["status"] == "active")

        return {
            "total_servers": total_servers,
            "active_servers": active_servers,
            "inactive_servers": total_servers - active_servers,
            "servers": {
                server_id: {
                    "status": info["status"],
                    "load": info["load"],
                    "last_health_check": info["last_health_check"].isoformat()
                }
                for server_id, info in self.servers.items()
            }
        }

class LoadBalancer:
    """负载均衡器"""

    def __init__(self, strategy: str = "round_robin"):
        self.strategy = strategy
        self.current_index = 0

    def select_server(self, available_servers: list) -> str:
        """选择服务器"""
        if not available_servers:
            raise ValueError("没有可用的服务器")

        if self.strategy == "round_robin":
            server_id = available_servers[self.current_index % len(available_servers)]
            self.current_index += 1
            return server_id
        elif self.strategy == "least_load":
            # 选择负载最低的服务器
            return min(available_servers, key=lambda s: s.get("load", 0))
        else:
            # 默认选择第一个
            return available_servers[0]
```

## 🔧 常见问题

### Q1: 如何处理服务器的并发请求？

**答：** 使用异步处理和连接池：

```python
import asyncio
from asyncio import Semaphore

class ConcurrentMCPServer(CustomMCPServer):
    def __init__(self, max_concurrent: int = 10):
        super().__init__()
        self.semaphore = Semaphore(max_concurrent)

    async def handle_request(self, request):
        async with self.semaphore:
            # 处理请求
            return await super().handle_request(request)
```

### Q2: 如何实现服务器的安全认证？

**答：** 添加认证中间件：

```python
class AuthenticatedMCPServer(CustomMCPServer):
    def __init__(self, api_keys: set):
        super().__init__()
        self.api_keys = api_keys

    def authenticate(self, request):
        api_key = request.headers.get("Authorization")
        return api_key in self.api_keys
```

### Q3: 如何优化服务器性能？

**答：** 使用缓存、连接池和异步处理：

```python
from functools import lru_cache
import aioredis

class OptimizedMCPServer(CustomMCPServer):
    def __init__(self):
        super().__init__()
        self.redis = None
        self.connection_pool = None

    @lru_cache(maxsize=100)
    def cached_operation(self, key):
        # 缓存频繁操作
        pass

    async def setup_redis(self):
        self.redis = await aioredis.create_redis_pool('redis://localhost')
```

## 📖 相关资源

### 官方文档
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### 下一步学习
- [15. MCP 集成教学](15_mcp_integration_tutorial.md) - 客户端集成
- [04. 自定义工具教学](04_custom_tools_tutorial.md) - 工具设计

### 代码示例
- 完整代码：[16_custom_mcp_server.py](../../teach_code/16_custom_mcp_server.py)
- 运行方式：`python teach_code/16_custom_mcp_server.py --server-type calculator`

## 🌟 总结

自定义 MCP 服务器为 AI 应用提供了无限的扩展可能：

1. **标准化协议**：遵循 MCP 规范，确保兼容性
2. **模块化设计**：清晰的架构分层和职责分离
3. **安全可靠**：完善的错误处理和安全机制
4. **高性能**：支持并发、缓存和负载均衡
5. **易于维护**：完整的监控、日志和配置管理

掌握自定义 MCP 服务器后，你可以为任何业务场景创建专门的工具服务！
