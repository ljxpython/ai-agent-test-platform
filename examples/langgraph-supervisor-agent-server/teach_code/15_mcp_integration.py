"""
MCP (Model Context Protocol) 集成示例
注意：这个示例需要 MCP 服务器运行
如果没有 MCP 服务器，代码会回退到模拟模式
"""

import asyncio
from typing import Annotated

from config import llm
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict


# 模拟 MCP 工具（当真实 MCP 不可用时）
@tool
def mock_math_add(a: float, b: float) -> float:
    """模拟数学加法工具"""
    return a + b


@tool
def mock_math_multiply(a: float, b: float) -> float:
    """模拟数学乘法工具"""
    return a * b


@tool
def mock_weather_get(city: str) -> str:
    """模拟天气查询工具"""
    weather_data = {
        "北京": "晴天，温度 15°C",
        "上海": "多云，温度 18°C",
        "深圳": "小雨，温度 22°C",
    }
    return weather_data.get(city, f"{city}的天气信息暂不可用")


@tool
def mock_file_read(filename: str) -> str:
    """模拟文件读取工具"""
    mock_files = {
        "config.txt": "# 配置文件\napi_key=test123\nport=8080",
        "data.csv": "name,age,city\n张三,25,北京\n李四,30,上海",
        "log.txt": "2024-01-01 10:00:00 INFO 系统启动\n2024-01-01 10:01:00 INFO 用户登录",
    }
    return mock_files.get(filename, f"文件 {filename} 不存在")


# 尝试导入 MCP 适配器
try:
    # 注意：这个导入可能失败，因为 MCP 适配器可能未安装
    # from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = False  # 暂时设为 False，因为 MCP 适配器可能未安装
    print("MCP 适配器不可用，使用模拟工具")
except ImportError:
    MCP_AVAILABLE = False
    print("MCP 适配器不可用，使用模拟工具")


async def create_mcp_tools():
    """创建 MCP 工具"""
    if not MCP_AVAILABLE:
        return [mock_math_add, mock_math_multiply, mock_weather_get, mock_file_read]

    try:
        # 配置 MCP 服务器（示例配置）
        # client = MultiServerMCPClient({
        #     "math": {
        #         "command": "python",
        #         "args": ["./examples/math_server.py"],
        #         "transport": "stdio",
        #     },
        #     "weather": {
        #         "url": "http://localhost:8000/mcp/",
        #         "transport": "streamable_http",
        #     }
        # })

        # 获取工具
        # tools = await client.get_tools()
        # print(f"成功连接 MCP，获得 {len(tools)} 个工具")
        # return tools

        # 由于实际 MCP 服务器可能不可用，返回模拟工具
        return [mock_math_add, mock_math_multiply, mock_weather_get, mock_file_read]

    except Exception as e:
        print(f"MCP 连接失败: {e}")
        print("回退到模拟工具")
        return [mock_math_add, mock_math_multiply, mock_weather_get, mock_file_read]


def should_continue(state: MessagesState):
    """判断是否继续执行工具"""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


async def call_model(state: MessagesState):
    """调用模型"""
    messages = state["messages"]
    response = await llm.ainvoke(messages)
    return {"messages": [response]}


async def create_mcp_graph():
    """创建 MCP 图"""
    # 获取工具
    tools = await create_mcp_tools()

    # 绑定工具到模型
    model_with_tools = llm.bind_tools(tools)

    def call_model_sync(state: MessagesState):
        """同步调用模型"""
        messages = state["messages"]
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}

    # 创建工具节点
    tool_node = ToolNode(tools)

    # 构建图
    builder = StateGraph(MessagesState)
    builder.add_node("call_model", call_model_sync)
    builder.add_node("tools", tool_node)

    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", should_continue)
    builder.add_edge("tools", "call_model")

    return builder.compile()


def run_mcp_demo():
    """运行 MCP 演示"""
    print("MCP 集成演示启动！")
    print("这个演示展示如何集成 MCP 工具。")
    print("可以尝试数学计算、天气查询或文件读取。")
    print("输入 'quit' 退出。")

    # 创建图（同步方式）
    try:
        graph = asyncio.run(create_mcp_graph())
    except Exception as e:
        print(f"创建图失败: {e}")
        return

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 调用图
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]}
            )

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")


# 异步版本的演示
async def run_async_mcp_demo():
    """运行异步 MCP 演示"""
    print("\n异步 MCP 演示启动！")

    # 创建图
    graph = await create_mcp_graph()

    # 测试用例
    test_cases = [
        "计算 (3 + 5) × 12",
        "北京的天气怎么样？",
        "计算 15 × 8 + 7",
        "上海今天天气如何？",
        "读取 config.txt 文件",
        "读取 data.csv 文件",
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n=== 测试 {i}: {test_input} ===")

        try:
            result = graph.invoke(
                {"messages": [{"role": "user", "content": test_input}]}
            )

            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"回复: {assistant_message.content}")

        except Exception as e:
            print(f"错误: {e}")


def demo_mcp_tool_discovery():
    """演示 MCP 工具发现"""
    print("\n" + "=" * 50)
    print("MCP 工具发现演示")
    print("=" * 50)

    async def discover_tools():
        tools = await create_mcp_tools()

        print("发现的工具:")
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
            if hasattr(tool, "args_schema") and tool.args_schema:
                print(f"  参数: {tool.args_schema.schema()}")

        return tools

    try:
        tools = asyncio.run(discover_tools())
        print(f"\n总共发现 {len(tools)} 个工具")
    except Exception as e:
        print(f"工具发现失败: {e}")


def demo_mcp_error_handling():
    """演示 MCP 错误处理"""
    print("\n" + "=" * 50)
    print("MCP 错误处理演示")
    print("=" * 50)

    # 测试各种错误情况
    error_test_cases = [
        ("计算 abc + def", "无效的数学表达式"),
        ("查询火星天气", "不支持的城市"),
        ("读取 nonexistent.txt", "文件不存在"),
        ("", "空输入"),
    ]

    async def test_error_handling():
        graph = await create_mcp_graph()

        for test_input, expected_error in error_test_cases:
            print(f"\n测试错误情况: '{test_input}'")
            print(f"预期错误类型: {expected_error}")

            try:
                result = graph.invoke(
                    {"messages": [{"role": "user", "content": test_input}]}
                )

                if result.get("messages"):
                    assistant_message = result["messages"][-1]
                    print(f"系统回复: {assistant_message.content}")

            except Exception as e:
                print(f"捕获异常: {e}")

    try:
        asyncio.run(test_error_handling())
    except Exception as e:
        print(f"错误处理测试失败: {e}")


def demo_mcp_performance():
    """演示 MCP 性能测试"""
    print("\n" + "=" * 50)
    print("MCP 性能测试演示")
    print("=" * 50)

    import time

    async def performance_test():
        graph = await create_mcp_graph()

        # 批量测试
        test_requests = [
            "计算 1 + 1",
            "计算 2 × 3",
            "计算 4 + 5",
            "计算 6 × 7",
            "计算 8 + 9",
        ]

        print("开始性能测试...")
        start_time = time.time()

        for i, request in enumerate(test_requests, 1):
            request_start = time.time()

            result = graph.invoke({"messages": [{"role": "user", "content": request}]})

            request_end = time.time()
            request_time = request_end - request_start

            print(f"请求 {i}: {request_time:.3f}s")

        total_time = time.time() - start_time
        avg_time = total_time / len(test_requests)

        print(f"\n性能统计:")
        print(f"总时间: {total_time:.3f}s")
        print(f"平均时间: {avg_time:.3f}s")
        print(f"吞吐量: {len(test_requests)/total_time:.2f} 请求/秒")

    try:
        asyncio.run(performance_test())
    except Exception as e:
        print(f"性能测试失败: {e}")


def demo_mcp_configuration():
    """演示 MCP 配置管理"""
    print("\n" + "=" * 50)
    print("MCP 配置管理演示")
    print("=" * 50)

    # 模拟不同的 MCP 配置
    configurations = [
        {
            "name": "本地数学服务",
            "type": "stdio",
            "command": "python math_server.py",
            "tools": ["add", "multiply", "divide"],
        },
        {
            "name": "天气API服务",
            "type": "http",
            "url": "http://weather-api.com/mcp",
            "tools": ["get_weather", "get_forecast"],
        },
        {
            "name": "文件系统服务",
            "type": "stdio",
            "command": "python file_server.py",
            "tools": ["read_file", "write_file", "list_files"],
        },
    ]

    print("可用的 MCP 配置:")
    for i, config in enumerate(configurations, 1):
        print(f"\n{i}. {config['name']}")
        print(f"   类型: {config['type']}")
        print(f"   工具: {', '.join(config['tools'])}")

        if config["type"] == "stdio":
            print(f"   命令: {config['command']}")
        elif config["type"] == "http":
            print(f"   URL: {config['url']}")

    print("\n注意：这些是示例配置，实际使用时需要相应的 MCP 服务器")


if __name__ == "__main__":
    run_mcp_demo()

    # 运行其他演示
    print("\n" + "=" * 50)
    asyncio.run(run_async_mcp_demo())
    demo_mcp_tool_discovery()
    demo_mcp_error_handling()
    demo_mcp_performance()
    demo_mcp_configuration()
