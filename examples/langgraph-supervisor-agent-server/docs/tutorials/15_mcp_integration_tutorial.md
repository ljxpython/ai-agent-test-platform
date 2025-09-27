# 15. MCP 集成教学

## 🎯 学习目标

通过这个教程，你将学会：
- MCP (Model Context Protocol) 的概念和架构
- 如何集成 MCP 客户端到 LangGraph
- 使用 MCP 工具扩展应用功能
- MCP 的最佳实践和故障处理

## 📚 核心概念

### 1. 什么是 MCP？

MCP (Model Context Protocol) 是一个**标准化的工具集成协议**，允许 AI 应用连接到各种外部服务：

```
LangGraph 应用 ← MCP 客户端 ← MCP 协议 → MCP 服务器 → 外部服务
```

**MCP 的优势：**
- **标准化**：统一的工具接口协议
- **可扩展**：轻松添加新的外部服务
- **安全性**：受控的工具访问机制
- **互操作性**：跨平台、跨语言支持

### 2. MCP 架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangGraph     │    │   MCP Client    │    │   MCP Server    │
│   Application   │◄──►│                 │◄──►│                 │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │ External Service │
                                               │ (File System,   │
                                               │  Database, API) │
                                               └─────────────────┘
```

### 3. MCP 工具类型

- **文件系统工具**：读写文件、目录操作
- **数据库工具**：查询、更新数据库
- **API 工具**：调用外部 REST/GraphQL API
- **系统工具**：执行系统命令、环境变量

## 🔍 代码详细解析

### 基础 MCP 客户端设置

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientManager:
    """MCP 客户端管理器"""

    def __init__(self):
        self.clients = {}
        self.available_tools = {}

    async def connect_to_server(self, server_name: str, server_command: list):
        """连接到 MCP 服务器"""
        try:
            # 创建服务器参数
            server_params = StdioServerParameters(
                command=server_command[0],
                args=server_command[1:] if len(server_command) > 1 else []
            )

            # 建立连接
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # 初始化会话
                    await session.initialize()

                    # 获取可用工具
                    tools_result = await session.list_tools()

                    self.clients[server_name] = session
                    self.available_tools[server_name] = tools_result.tools

                    print(f"已连接到 MCP 服务器: {server_name}")
                    print(f"可用工具: {len(tools_result.tools)} 个")

                    return session

        except Exception as e:
            print(f"连接 MCP 服务器失败: {e}")
            return None

    def get_available_tools(self, server_name: str = None):
        """获取可用工具"""
        if server_name:
            return self.available_tools.get(server_name, [])

        # 返回所有服务器的工具
        all_tools = []
        for tools in self.available_tools.values():
            all_tools.extend(tools)
        return all_tools

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict):
        """调用 MCP 工具"""
        if server_name not in self.clients:
            raise ValueError(f"未连接到服务器: {server_name}")

        session = self.clients[server_name]

        try:
            # 调用工具
            result = await session.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            print(f"调用工具失败: {e}")
            return {"error": str(e)}

# 创建 MCP 客户端管理器
mcp_manager = MCPClientManager()
```

### LangGraph 集成

```python
from langchain_core.tools import tool
from typing_extensions import TypedDict

class MCPState(TypedDict):
    messages: list
    mcp_results: dict
    error_message: str

# 创建 MCP 工具包装器
def create_mcp_tool(server_name: str, tool_name: str, tool_description: str):
    """创建 MCP 工具包装器"""

    @tool
    async def mcp_tool_wrapper(**kwargs) -> str:
        f"""
        {tool_description}

        Args:
            **kwargs: 工具参数
        """
        try:
            result = await mcp_manager.call_tool(server_name, tool_name, kwargs)

            if "error" in result:
                return f"工具调用失败: {result['error']}"

            # 处理结果
            if hasattr(result, 'content'):
                return str(result.content)
            else:
                return str(result)

        except Exception as e:
            return f"MCP 工具调用异常: {e}"

    # 设置工具名称
    mcp_tool_wrapper.name = f"mcp_{server_name}_{tool_name}"
    return mcp_tool_wrapper

async def setup_mcp_tools():
    """设置 MCP 工具"""
    # 连接到文件系统服务器（示例）
    filesystem_server = await mcp_manager.connect_to_server(
        "filesystem",
        ["python", "-m", "mcp_server_filesystem"]
    )

    if filesystem_server:
        # 创建文件系统工具
        read_file_tool = create_mcp_tool(
            "filesystem",
            "read_file",
            "读取文件内容。参数: path (文件路径)"
        )

        write_file_tool = create_mcp_tool(
            "filesystem",
            "write_file",
            "写入文件内容。参数: path (文件路径), content (文件内容)"
        )

        list_directory_tool = create_mcp_tool(
            "filesystem",
            "list_directory",
            "列出目录内容。参数: path (目录路径)"
        )

        return [read_file_tool, write_file_tool, list_directory_tool]

    return []

def mcp_chatbot(state: MCPState):
    """带 MCP 工具的聊天机器人"""
    messages = state["messages"]

    # 这里需要异步处理，实际实现可能需要调整
    # 为了演示，我们返回一个简化的响应

    response_content = "我可以帮您操作文件系统。请告诉我您需要读取、写入或列出哪些文件。"

    return {
        "messages": messages + [{"role": "assistant", "content": response_content}]
    }

# 构建带 MCP 的图
async def create_mcp_graph():
    """创建带 MCP 工具的图"""
    # 设置 MCP 工具
    mcp_tools = await setup_mcp_tools()

    if not mcp_tools:
        print("警告: 没有可用的 MCP 工具")
        mcp_tools = []

    # 绑定工具到 LLM
    llm_with_mcp_tools = llm.bind_tools(mcp_tools)

    def enhanced_chatbot(state: MCPState):
        """增强的聊天机器人"""
        return {"messages": [llm_with_mcp_tools.invoke(state["messages"])]}

    # 构建图
    builder = StateGraph(MCPState)
    builder.add_node("chatbot", enhanced_chatbot)

    if mcp_tools:
        from langgraph.prebuilt import ToolNode, tools_condition
        tool_node = ToolNode(tools=mcp_tools)
        builder.add_node("tools", tool_node)
        builder.add_conditional_edges("chatbot", tools_condition)
        builder.add_edge("tools", "chatbot")

    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)

    return builder.compile()
```

### MCP 工具演示

```python
async def run_mcp_demo():
    """运行 MCP 演示"""
    print("MCP 集成演示启动！")

    try:
        # 创建带 MCP 的图
        mcp_graph = await create_mcp_graph()

        print("可用的 MCP 工具:")
        for server_name, tools in mcp_manager.available_tools.items():
            print(f"  服务器 {server_name}:")
            for tool in tools:
                print(f"    - {tool.name}: {tool.description}")

        # 测试用例
        test_cases = [
            "请列出当前目录的文件",
            "读取 README.md 文件的内容",
            "创建一个名为 test.txt 的文件，内容是 'Hello MCP!'"
        ]

        for i, test_input in enumerate(test_cases, 1):
            print(f"\n=== 测试案例 {i} ===")
            print(f"用户: {test_input}")

            try:
                result = mcp_graph.invoke({
                    "messages": [{"role": "user", "content": test_input}],
                    "mcp_results": {},
                    "error_message": ""
                })

                if result.get("messages"):
                    assistant_message = result["messages"][-1]
                    print(f"助手: {assistant_message.get('content', '无回复')}")

            except Exception as e:
                print(f"处理错误: {e}")

    except Exception as e:
        print(f"MCP 演示失败: {e}")

# 运行演示
# asyncio.run(run_mcp_demo())
```

## 🚀 高级 MCP 模式

### 1. 多服务器管理

```python
class AdvancedMCPManager:
    """高级 MCP 管理器"""

    def __init__(self):
        self.server_configs = {}
        self.connection_pool = {}
        self.tool_registry = {}
        self.health_status = {}

    def register_server(self, server_name: str, config: dict):
        """注册 MCP 服务器"""
        self.server_configs[server_name] = {
            "command": config["command"],
            "args": config.get("args", []),
            "retry_count": config.get("retry_count", 3),
            "timeout": config.get("timeout", 30),
            "health_check_interval": config.get("health_check_interval", 60)
        }

        print(f"注册 MCP 服务器: {server_name}")

    async def connect_all_servers(self):
        """连接所有注册的服务器"""
        connection_tasks = []

        for server_name, config in self.server_configs.items():
            task = self._connect_with_retry(server_name, config)
            connection_tasks.append(task)

        # 并行连接所有服务器
        results = await asyncio.gather(*connection_tasks, return_exceptions=True)

        successful_connections = 0
        for i, result in enumerate(results):
            server_name = list(self.server_configs.keys())[i]

            if isinstance(result, Exception):
                print(f"连接 {server_name} 失败: {result}")
                self.health_status[server_name] = "failed"
            else:
                print(f"连接 {server_name} 成功")
                self.health_status[server_name] = "healthy"
                successful_connections += 1

        print(f"成功连接 {successful_connections}/{len(self.server_configs)} 个服务器")

    async def _connect_with_retry(self, server_name: str, config: dict):
        """带重试的连接"""
        retry_count = config["retry_count"]

        for attempt in range(retry_count):
            try:
                command = [config["command"]] + config["args"]
                session = await mcp_manager.connect_to_server(server_name, command)

                if session:
                    self.connection_pool[server_name] = session
                    await self._register_tools(server_name, session)
                    return session

            except Exception as e:
                print(f"连接 {server_name} 第 {attempt + 1} 次尝试失败: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # 指数退避

        raise Exception(f"连接 {server_name} 失败，已重试 {retry_count} 次")

    async def _register_tools(self, server_name: str, session):
        """注册服务器工具"""
        try:
            tools_result = await session.list_tools()

            for tool in tools_result.tools:
                tool_id = f"{server_name}.{tool.name}"
                self.tool_registry[tool_id] = {
                    "server": server_name,
                    "tool": tool,
                    "session": session
                }

            print(f"注册了 {len(tools_result.tools)} 个工具从服务器 {server_name}")

        except Exception as e:
            print(f"注册工具失败 {server_name}: {e}")

    async def health_check(self):
        """健康检查"""
        for server_name, session in self.connection_pool.items():
            try:
                # 尝试列出工具作为健康检查
                await session.list_tools()
                self.health_status[server_name] = "healthy"
            except Exception as e:
                print(f"健康检查失败 {server_name}: {e}")
                self.health_status[server_name] = "unhealthy"

    def get_health_report(self) -> dict:
        """获取健康报告"""
        total_servers = len(self.server_configs)
        healthy_servers = sum(1 for status in self.health_status.values() if status == "healthy")

        return {
            "total_servers": total_servers,
            "healthy_servers": healthy_servers,
            "unhealthy_servers": total_servers - healthy_servers,
            "health_percentage": (healthy_servers / total_servers * 100) if total_servers > 0 else 0,
            "server_status": self.health_status,
            "available_tools": len(self.tool_registry)
        }

# 使用高级管理器
advanced_mcp = AdvancedMCPManager()

# 注册多个服务器
advanced_mcp.register_server("filesystem", {
    "command": "python",
    "args": ["-m", "mcp_server_filesystem"],
    "retry_count": 3
})

advanced_mcp.register_server("database", {
    "command": "python",
    "args": ["-m", "mcp_server_database"],
    "retry_count": 2
})
```

### 2. MCP 工具缓存

```python
import hashlib
import json
from datetime import datetime, timedelta

class MCPToolCache:
    """MCP 工具缓存"""

    def __init__(self, default_ttl: int = 300):  # 5分钟默认TTL
        self.cache = {}
        self.default_ttl = default_ttl
        self.hit_count = 0
        self.miss_count = 0

    def _generate_cache_key(self, server_name: str, tool_name: str, arguments: dict) -> str:
        """生成缓存键"""
        cache_data = {
            "server": server_name,
            "tool": tool_name,
            "args": arguments
        }

        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def get(self, server_name: str, tool_name: str, arguments: dict):
        """获取缓存结果"""
        cache_key = self._generate_cache_key(server_name, tool_name, arguments)

        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]

            # 检查是否过期
            if datetime.now() < cache_entry["expires_at"]:
                self.hit_count += 1
                print(f"缓存命中: {tool_name}")
                return cache_entry["result"]
            else:
                # 删除过期条目
                del self.cache[cache_key]

        self.miss_count += 1
        return None

    def set(self, server_name: str, tool_name: str, arguments: dict, result, ttl: int = None):
        """设置缓存结果"""
        cache_key = self._generate_cache_key(server_name, tool_name, arguments)
        ttl = ttl or self.default_ttl

        cache_entry = {
            "result": result,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "server": server_name,
            "tool": tool_name
        }

        self.cache[cache_key] = cache_entry
        print(f"缓存设置: {tool_name} (TTL: {ttl}s)")

    def invalidate(self, server_name: str = None, tool_name: str = None):
        """失效缓存"""
        to_remove = []

        for cache_key, cache_entry in self.cache.items():
            should_remove = True

            if server_name and cache_entry["server"] != server_name:
                should_remove = False

            if tool_name and cache_entry["tool"] != tool_name:
                should_remove = False

            if should_remove:
                to_remove.append(cache_key)

        for cache_key in to_remove:
            del self.cache[cache_key]

        print(f"失效了 {len(to_remove)} 个缓存条目")

    def cleanup_expired(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry["expires_at"]
        ]

        for key in expired_keys:
            del self.cache[key]

        print(f"清理了 {len(expired_keys)} 个过期缓存条目")

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_entries": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

# 使用缓存
mcp_cache = MCPToolCache()

async def cached_mcp_call(server_name: str, tool_name: str, arguments: dict):
    """带缓存的 MCP 调用"""
    # 尝试从缓存获取
    cached_result = mcp_cache.get(server_name, tool_name, arguments)
    if cached_result is not None:
        return cached_result

    # 缓存未命中，调用实际工具
    result = await mcp_manager.call_tool(server_name, tool_name, arguments)

    # 缓存结果（如果成功）
    if "error" not in result:
        # 根据工具类型设置不同的TTL
        ttl = 60 if tool_name.startswith("read") else 300
        mcp_cache.set(server_name, tool_name, arguments, result, ttl)

    return result
```

### 3. MCP 错误处理和重试

```python
import asyncio
from enum import Enum

class MCPErrorType(Enum):
    CONNECTION_ERROR = "connection_error"
    TIMEOUT_ERROR = "timeout_error"
    TOOL_ERROR = "tool_error"
    PERMISSION_ERROR = "permission_error"
    UNKNOWN_ERROR = "unknown_error"

class MCPErrorHandler:
    """MCP 错误处理器"""

    def __init__(self):
        self.error_counts = {}
        self.circuit_breakers = {}
        self.retry_strategies = {
            MCPErrorType.CONNECTION_ERROR: {"max_retries": 3, "backoff": "exponential"},
            MCPErrorType.TIMEOUT_ERROR: {"max_retries": 2, "backoff": "linear"},
            MCPErrorType.TOOL_ERROR: {"max_retries": 1, "backoff": "none"},
            MCPErrorType.PERMISSION_ERROR: {"max_retries": 0, "backoff": "none"},
            MCPErrorType.UNKNOWN_ERROR: {"max_retries": 1, "backoff": "linear"}
        }

    def classify_error(self, error: Exception) -> MCPErrorType:
        """分类错误类型"""
        error_str = str(error).lower()

        if "connection" in error_str or "connect" in error_str:
            return MCPErrorType.CONNECTION_ERROR
        elif "timeout" in error_str:
            return MCPErrorType.TIMEOUT_ERROR
        elif "permission" in error_str or "unauthorized" in error_str:
            return MCPErrorType.PERMISSION_ERROR
        elif "tool" in error_str or "method" in error_str:
            return MCPErrorType.TOOL_ERROR
        else:
            return MCPErrorType.UNKNOWN_ERROR

    async def handle_with_retry(self, server_name: str, tool_name: str, arguments: dict, call_func):
        """带重试的错误处理"""
        error_key = f"{server_name}.{tool_name}"

        # 检查熔断器
        if self._is_circuit_open(error_key):
            return {"error": "服务暂时不可用（熔断器开启）"}

        last_error = None

        for attempt in range(3):  # 最大3次尝试
            try:
                result = await call_func(server_name, tool_name, arguments)

                # 成功时重置错误计数
                if error_key in self.error_counts:
                    self.error_counts[error_key] = 0

                return result

            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)

                # 记录错误
                self._record_error(error_key)

                # 获取重试策略
                strategy = self.retry_strategies.get(error_type, {"max_retries": 1, "backoff": "linear"})

                if attempt >= strategy["max_retries"]:
                    break

                # 计算退避时间
                backoff_time = self._calculate_backoff(strategy["backoff"], attempt)

                print(f"工具调用失败 (尝试 {attempt + 1}): {e}")
                print(f"等待 {backoff_time}s 后重试...")

                await asyncio.sleep(backoff_time)

        # 所有重试都失败
        return {"error": f"工具调用最终失败: {last_error}"}

    def _record_error(self, error_key: str):
        """记录错误"""
        if error_key not in self.error_counts:
            self.error_counts[error_key] = 0

        self.error_counts[error_key] += 1

        # 检查是否需要开启熔断器
        if self.error_counts[error_key] >= 5:
            self.circuit_breakers[error_key] = {
                "opened_at": datetime.now(),
                "timeout": 60  # 60秒后尝试恢复
            }
            print(f"熔断器开启: {error_key}")

    def _is_circuit_open(self, error_key: str) -> bool:
        """检查熔断器是否开启"""
        if error_key not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[error_key]
        timeout_time = breaker["opened_at"] + timedelta(seconds=breaker["timeout"])

        if datetime.now() > timeout_time:
            # 熔断器超时，尝试恢复
            del self.circuit_breakers[error_key]
            self.error_counts[error_key] = 0
            print(f"熔断器恢复: {error_key}")
            return False

        return True

    def _calculate_backoff(self, backoff_type: str, attempt: int) -> float:
        """计算退避时间"""
        if backoff_type == "exponential":
            return min(2 ** attempt, 30)  # 最大30秒
        elif backoff_type == "linear":
            return min(attempt * 2, 10)   # 最大10秒
        else:
            return 0

# 使用错误处理器
error_handler = MCPErrorHandler()

async def robust_mcp_call(server_name: str, tool_name: str, arguments: dict):
    """健壮的 MCP 调用"""
    return await error_handler.handle_with_retry(
        server_name,
        tool_name,
        arguments,
        mcp_manager.call_tool
    )
```

## 🎯 实践练习

### 练习1：文件管理助手

```python
class FileManagerAssistant:
    """文件管理助手"""

    def __init__(self, mcp_manager):
        self.mcp_manager = mcp_manager
        self.allowed_extensions = {'.txt', '.md', '.json', '.csv', '.log'}
        self.max_file_size = 10 * 1024 * 1024  # 10MB

    async def safe_read_file(self, file_path: str) -> str:
        """安全读取文件"""
        # 安全检查
        if not self._is_safe_path(file_path):
            return "错误：不安全的文件路径"

        if not self._is_allowed_extension(file_path):
            return f"错误：不支持的文件类型。支持的类型：{', '.join(self.allowed_extensions)}"

        try:
            result = await self.mcp_manager.call_tool(
                "filesystem",
                "read_file",
                {"path": file_path}
            )

            if "error" in result:
                return f"读取失败：{result['error']}"

            content = result.get("content", "")

            # 检查文件大小
            if len(content) > self.max_file_size:
                return f"错误：文件太大（{len(content)} 字节，最大 {self.max_file_size} 字节）"

            return f"文件内容：\n{content}"

        except Exception as e:
            return f"读取异常：{e}"

    async def safe_write_file(self, file_path: str, content: str) -> str:
        """安全写入文件"""
        # 安全检查
        if not self._is_safe_path(file_path):
            return "错误：不安全的文件路径"

        if not self._is_allowed_extension(file_path):
            return f"错误：不支持的文件类型"

        if len(content) > self.max_file_size:
            return f"错误：内容太大"

        try:
            result = await self.mcp_manager.call_tool(
                "filesystem",
                "write_file",
                {"path": file_path, "content": content}
            )

            if "error" in result:
                return f"写入失败：{result['error']}"

            return f"文件已写入：{file_path}"

        except Exception as e:
            return f"写入异常：{e}"

    def _is_safe_path(self, path: str) -> bool:
        """检查路径安全性"""
        # 防止路径遍历攻击
        if ".." in path or path.startswith("/"):
            return False

        # 只允许相对路径
        return True

    def _is_allowed_extension(self, path: str) -> bool:
        """检查文件扩展名"""
        import os
        _, ext = os.path.splitext(path)
        return ext.lower() in self.allowed_extensions

# 使用文件管理助手
file_assistant = FileManagerAssistant(mcp_manager)

async def demo_file_operations():
    """演示文件操作"""
    operations = [
        ("read", "README.md"),
        ("write", "test.txt", "Hello from MCP!"),
        ("read", "test.txt"),
        ("read", "../etc/passwd"),  # 应该被拒绝
    ]

    for operation in operations:
        if operation[0] == "read":
            result = await file_assistant.safe_read_file(operation[1])
            print(f"读取 {operation[1]}: {result[:100]}...")
        elif operation[0] == "write":
            result = await file_assistant.safe_write_file(operation[1], operation[2])
            print(f"写入 {operation[1]}: {result}")
```

### 练习2：MCP 监控仪表板

```python
class MCPMonitoringDashboard:
    """MCP 监控仪表板"""

    def __init__(self):
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "average_response_time": 0,
            "server_status": {},
            "tool_usage": {},
            "error_types": {}
        }
        self.call_history = []

    def record_call(self, server_name: str, tool_name: str, success: bool,
                   response_time: float, error_type: str = None):
        """记录调用"""
        self.metrics["total_calls"] += 1

        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1
            if error_type:
                self.metrics["error_types"][error_type] = \
                    self.metrics["error_types"].get(error_type, 0) + 1

        # 更新平均响应时间
        total_time = self.metrics["average_response_time"] * (self.metrics["total_calls"] - 1)
        self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_calls"]

        # 记录工具使用
        tool_key = f"{server_name}.{tool_name}"
        self.metrics["tool_usage"][tool_key] = \
            self.metrics["tool_usage"].get(tool_key, 0) + 1

        # 记录历史
        call_record = {
            "timestamp": datetime.now().isoformat(),
            "server": server_name,
            "tool": tool_name,
            "success": success,
            "response_time": response_time,
            "error_type": error_type
        }

        self.call_history.append(call_record)

        # 限制历史记录长度
        if len(self.call_history) > 1000:
            self.call_history = self.call_history[-1000:]

    def update_server_status(self, server_name: str, status: str):
        """更新服务器状态"""
        self.metrics["server_status"][server_name] = {
            "status": status,
            "last_updated": datetime.now().isoformat()
        }

    def get_dashboard_data(self) -> dict:
        """获取仪表板数据"""
        success_rate = 0
        if self.metrics["total_calls"] > 0:
            success_rate = (self.metrics["successful_calls"] / self.metrics["total_calls"]) * 100

        # 最近1小时的调用
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_calls = [
            call for call in self.call_history
            if datetime.fromisoformat(call["timestamp"]) > one_hour_ago
        ]

        return {
            "overview": {
                "total_calls": self.metrics["total_calls"],
                "success_rate": success_rate,
                "average_response_time": self.metrics["average_response_time"],
                "active_servers": len([
                    s for s in self.metrics["server_status"].values()
                    if s["status"] == "healthy"
                ])
            },
            "server_status": self.metrics["server_status"],
            "tool_usage": dict(sorted(
                self.metrics["tool_usage"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),  # 前10个最常用工具
            "error_types": self.metrics["error_types"],
            "recent_activity": len(recent_calls)
        }

    def print_dashboard(self):
        """打印仪表板"""
        data = self.get_dashboard_data()

        print("\n" + "="*60)
        print("MCP 监控仪表板")
        print("="*60)

        overview = data["overview"]
        print(f"总调用次数: {overview['total_calls']}")
        print(f"成功率: {overview['success_rate']:.1f}%")
        print(f"平均响应时间: {overview['average_response_time']:.3f}s")
        print(f"活跃服务器: {overview['active_servers']}")

        print(f"\n服务器状态:")
        for server, status in data["server_status"].items():
            status_icon = "✅" if status["status"] == "healthy" else "❌"
            print(f"  {status_icon} {server}: {status['status']}")

        print(f"\n热门工具:")
        for tool, count in list(data["tool_usage"].items())[:5]:
            print(f"  {tool}: {count} 次")

        if data["error_types"]:
            print(f"\n错误类型:")
            for error_type, count in data["error_types"].items():
                print(f"  {error_type}: {count} 次")

# 使用监控仪表板
monitoring = MCPMonitoringDashboard()

async def monitored_mcp_call(server_name: str, tool_name: str, arguments: dict):
    """带监控的 MCP 调用"""
    start_time = time.time()

    try:
        result = await mcp_manager.call_tool(server_name, tool_name, arguments)
        response_time = time.time() - start_time

        success = "error" not in result
        error_type = None if success else "tool_error"

        monitoring.record_call(server_name, tool_name, success, response_time, error_type)

        return result

    except Exception as e:
        response_time = time.time() - start_time
        error_type = error_handler.classify_error(e).value

        monitoring.record_call(server_name, tool_name, False, response_time, error_type)

        raise e
```

## 🔧 常见问题

### Q1: MCP 服务器连接失败怎么办？

**答：** 检查服务器配置和网络连接：

```python
async def diagnose_connection_issue(server_name: str, config: dict):
    """诊断连接问题"""
    print(f"诊断 {server_name} 连接问题...")

    # 检查命令是否存在
    command = config["command"]
    if not shutil.which(command):
        print(f"错误：命令 {command} 不存在")
        return False

    # 检查端口是否被占用
    # 检查权限
    # 检查依赖

    return True
```

### Q2: 如何处理 MCP 工具的权限问题？

**答：** 实现权限检查和沙箱机制：

```python
class MCPPermissionManager:
    def __init__(self):
        self.allowed_operations = {
            "filesystem": ["read_file", "list_directory"],
            "database": ["select"]
        }

    def check_permission(self, server_name: str, tool_name: str) -> bool:
        allowed = self.allowed_operations.get(server_name, [])
        return tool_name in allowed
```

### Q3: MCP 工具性能如何优化？

**答：** 使用连接池、缓存和批处理：

```python
# 连接池
class MCPConnectionPool:
    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)

    async def get_connection(self):
        return await self.pool.get()

    async def return_connection(self, connection):
        await self.pool.put(connection)
```

## 📖 相关资源

### 官方文档
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

### 下一步学习
- [16. 自定义 MCP 服务器教学](16_custom_mcp_server_tutorial.md) - 创建 MCP 服务器
- [04. 自定义工具教学](04_custom_tools_tutorial.md) - 工具设计对比

### 代码示例
- 完整代码：[15_mcp_integration.py](../../teach_code/15_mcp_integration.py)
- 运行方式：`python teach_code/15_mcp_integration.py`

## 🌟 总结

MCP 集成为 LangGraph 应用提供了强大的扩展能力：

1. **标准化接口**：统一的工具集成协议
2. **丰富生态**：可接入各种外部服务
3. **安全可控**：受控的工具访问机制
4. **高性能**：支持缓存、连接池等优化
5. **易于维护**：模块化的工具管理

掌握 MCP 集成后，你可以构建功能丰富的企业级应用！
