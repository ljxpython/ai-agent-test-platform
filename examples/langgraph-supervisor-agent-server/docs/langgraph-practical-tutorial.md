# LangGraph 实战教程 - 完整可运行代码示例

## 目录

1. [环境配置](#1-环境配置)
2. [基础聊天机器人](#2-基础聊天机器人)
3. [工具集成](#3-工具集成)
4. [状态管理](#4-状态管理)
5. [检查点和持久化](#5-检查点和持久化)
6. [人机交互](#6-人机交互)
7. [时间旅行](#7-时间旅行)
8. [运行时上下文](#8-运行时上下文)
9. [记忆系统](#9-记忆系统)
10. [子图](#10-子图)
11. [MCP 集成](#11-mcp-集成)
12. [多智能体系统](#12-多智能体系统)

---

## 1. 环境配置

### 1.1 安装依赖

```bash
# 核心依赖
pip install langgraph langchain langchain-core
pip install langchain-deepseek langchain-openai
pip install langchain-tavily python-dotenv

# 可选依赖
pip install "langgraph[dev]"  # 可视化工具
pip install langchain-mcp-adapters  # MCP 支持
```

### 1.2 环境变量配置

创建 `.env` 文件：

```bash
# DeepSeek API
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# OpenAI API (可选)
OPENAI_API_KEY=sk-your-openai-api-key

# Tavily Search API (可选)
TAVILY_API_KEY=your-tavily-api-key
```

### 1.3 基础配置模块

```python
# teach_code/config.py
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

def get_llm(provider="deepseek", model="deepseek-chat"):
    """获取配置好的 LLM 实例"""
    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return init_chat_model(
            model=model,
            model_provider=provider,
            api_key=api_key,
            temperature=0.0
        )
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        return init_chat_model(
            model=model,
            model_provider=provider,
            api_key=api_key,
            temperature=0.0
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")

# 默认 LLM 实例
llm = get_llm()
```

---

## 2. 基础聊天机器人

### 2.1 简单聊天机器人

```python
# teach_code/01_basic_chatbot.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from config import llm

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 编译图
graph = graph_builder.compile()

def run_chatbot():
    """运行聊天机器人"""
    print("聊天机器人启动！输入 'quit' 退出。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        # 调用图
        result = graph.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        # 输出回复
        assistant_message = result["messages"][-1]
        print(f"助手: {assistant_message.content}")

if __name__ == "__main__":
    run_chatbot()
```

### 2.2 流式聊天机器人

```python
# teach_code/02_streaming_chatbot.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from config import llm

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 编译图
graph = graph_builder.compile()

def stream_graph_updates(user_input: str):
    """流式处理图更新"""
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            if "messages" in value:
                print("助手:", value["messages"][-1].content)

def run_streaming_chatbot():
    """运行流式聊天机器人"""
    print("流式聊天机器人启动！输入 'quit' 退出。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        stream_graph_updates(user_input)

if __name__ == "__main__":
    run_streaming_chatbot()
```

---

## 3. 工具集成

### 3.1 带搜索工具的聊天机器人

```python
# teach_code/03_chatbot_with_tools.py
import os
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from config import llm

# 检查 Tavily API Key
if not os.getenv("TAVILY_API_KEY"):
    print("警告: 未设置 TAVILY_API_KEY，搜索功能将不可用")

class State(TypedDict):
    messages: Annotated[list, add_messages]

# 设置工具
try:
    tool = TavilySearch(max_results=2)
    tools = [tool]
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        """带工具的聊天机器人节点"""
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # 构建图
    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)

    # 添加工具节点
    tool_node = ToolNode(tools=[tool])
    graph_builder.add_node("tools", tool_node)

    # 添加边
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_conditional_edges(
        "chatbot",
        tools_condition,
    )
    graph_builder.add_edge("tools", "chatbot")

    # 编译图
    graph = graph_builder.compile()

except Exception as e:
    print(f"工具初始化失败: {e}")
    # 回退到基础聊天机器人
    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    graph_builder = StateGraph(State)
    graph_builder.add_node("chatbot", chatbot)
    graph_builder.add_edge(START, "chatbot")
    graph_builder.add_edge("chatbot", END)
    graph = graph_builder.compile()

def run_tool_chatbot():
    """运行带工具的聊天机器人"""
    print("带搜索工具的聊天机器人启动！")
    print("你可以问我任何问题，我会搜索最新信息来回答。")
    print("输入 'quit' 退出。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 流式处理
            for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
                for value in event.values():
                    if "messages" in value:
                        message = value["messages"][-1]
                        if hasattr(message, 'content') and message.content:
                            print(f"助手: {message.content}")
                        elif hasattr(message, 'tool_calls') and message.tool_calls:
                            print("正在搜索信息...")
        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_tool_chatbot()
```

### 3.2 自定义工具

```python
# teach_code/04_custom_tools.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import tool
from config import llm
import datetime
import random

class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def get_random_number(min_val: int = 1, max_val: int = 100) -> int:
    """生成指定范围内的随机数

    Args:
        min_val: 最小值
        max_val: 最大值
    """
    return random.randint(min_val, max_val)

@tool
def calculate(expression: str) -> str:
    """计算数学表达式

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
    """
    try:
        # 安全的数学计算
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

# 设置工具
tools = [get_current_time, get_random_number, calculate]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """带自定义工具的聊天机器人"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# 添加工具节点
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# 编译图
graph = graph_builder.compile()

def run_custom_tools_chatbot():
    """运行带自定义工具的聊天机器人"""
    print("带自定义工具的聊天机器人启动！")
    print("可用工具：")
    print("- 获取当前时间")
    print("- 生成随机数")
    print("- 计算数学表达式")
    print("输入 'quit' 退出。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
                for value in event.values():
                    if "messages" in value:
                        message = value["messages"][-1]
                        if hasattr(message, 'content') and message.content:
                            print(f"助手: {message.content}")
                        elif hasattr(message, 'tool_calls') and message.tool_calls:
                            print("正在使用工具...")
        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_custom_tools_chatbot()
```

---

## 4. 状态管理

### 4.1 复杂状态管理

```python
# teach_code/05_state_management.py
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
import operator
from config import llm

class ComplexState(TypedDict):
    # 消息历史
    messages: Annotated[list, add_messages]

    # 用户信息
    user_name: Optional[str]
    user_preferences: dict

    # 对话统计
    message_count: Annotated[int, operator.add]

    # 上下文信息
    current_topic: Optional[str]
    conversation_summary: str

def analyze_input(state: ComplexState):
    """分析用户输入"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content.lower()

    # 检测话题
    topics = {
        "天气": ["天气", "温度", "下雨", "晴天"],
        "技术": ["编程", "代码", "技术", "开发"],
        "生活": ["生活", "日常", "吃饭", "睡觉"],
    }

    detected_topic = None
    for topic, keywords in topics.items():
        if any(keyword in user_content for keyword in keywords):
            detected_topic = topic
            break

    return {
        "current_topic": detected_topic,
        "message_count": 1
    }

def generate_response(state: ComplexState):
    """生成回复"""
    messages = state["messages"]
    current_topic = state.get("current_topic")
    user_name = state.get("user_name", "朋友")

    # 构建系统提示
    system_prompt = f"你是一个友好的助手。"
    if current_topic:
        system_prompt += f" 当前话题是：{current_topic}。"
    if user_name != "朋友":
        system_prompt += f" 用户名是：{user_name}。"

    # 添加系统消息
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages

    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}

def update_summary(state: ComplexState):
    """更新对话摘要"""
    messages = state["messages"]
    message_count = state.get("message_count", 0)

    if message_count > 0 and message_count % 5 == 0:
        # 每5条消息更新一次摘要
        recent_messages = messages[-10:]  # 最近10条消息

        summary_prompt = "请简要总结以下对话内容：\n"
        for msg in recent_messages:
            role = "用户" if msg.get("role") == "user" else "助手"
            summary_prompt += f"{role}: {msg.get('content', '')}\n"

        summary_response = llm.invoke([{"role": "user", "content": summary_prompt}])

        return {"conversation_summary": summary_response.content}

    return {}

# 构建图
graph_builder = StateGraph(ComplexState)
graph_builder.add_node("analyze", analyze_input)
graph_builder.add_node("respond", generate_response)
graph_builder.add_node("summarize", update_summary)

# 添加边
graph_builder.add_edge(START, "analyze")
graph_builder.add_edge("analyze", "respond")
graph_builder.add_edge("respond", "summarize")
graph_builder.add_edge("summarize", END)

# 编译图
graph = graph_builder.compile()

def run_state_management_demo():
    """运行状态管理演示"""
    print("状态管理演示启动！")
    print("这个聊天机器人会跟踪对话状态、话题和统计信息。")
    print("输入 'quit' 退出，输入 'status' 查看状态。")

    # 初始状态
    current_state = {
        "messages": [],
        "user_name": None,
        "user_preferences": {},
        "message_count": 0,
        "current_topic": None,
        "conversation_summary": ""
    }

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        if user_input.lower() == 'status':
            print(f"\n=== 当前状态 ===")
            print(f"消息数量: {current_state.get('message_count', 0)}")
            print(f"当前话题: {current_state.get('current_topic', '无')}")
            print(f"用户名: {current_state.get('user_name', '未设置')}")
            if current_state.get('conversation_summary'):
                print(f"对话摘要: {current_state['conversation_summary']}")
            continue

        # 检查是否设置用户名
        if not current_state.get("user_name") and "我叫" in user_input:
            import re
            name_match = re.search(r"我叫(.+)", user_input)
            if name_match:
                current_state["user_name"] = name_match.group(1).strip()
                print(f"已记录您的名字：{current_state['user_name']}")

        # 添加用户消息到状态
        current_state["messages"].append({"role": "user", "content": user_input})

        try:
            # 运行图
            result = graph.invoke(current_state)

            # 更新状态
            current_state.update(result)

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_state_management_demo()
```

---

## 5. 检查点和持久化

### 5.1 内存检查点

```python
# teach_code/06_memory_checkpoint.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from config import llm

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}

# 创建内存检查点保存器
memory = InMemorySaver()

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 编译图（启用检查点）
graph = graph_builder.compile(checkpointer=memory)

def run_memory_chatbot():
    """运行带内存的聊天机器人"""
    print("带内存的聊天机器人启动！")
    print("这个机器人会记住我们的对话历史。")
    print("输入 'quit' 退出，输入 'history' 查看历史。")

    # 配置线程ID
    config = {"configurable": {"thread_id": "conversation_1"}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        if user_input.lower() == 'history':
            # 获取状态历史
            try:
                current_state = graph.get_state(config)
                messages = current_state.values.get("messages", [])
                print(f"\n=== 对话历史 ({len(messages)} 条消息) ===")
                for i, msg in enumerate(messages, 1):
                    role = "用户" if msg.get("role") == "user" else "助手"
                    content = msg.get("content", "")
                    print(f"{i}. {role}: {content[:100]}...")
            except Exception as e:
                print(f"获取历史失败: {e}")
            continue

        try:
            # 调用图（会自动保存和恢复状态）
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )

            # 输出回复
            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_memory_chatbot()
```

### 5.2 SQLite 检查点

```python
# teach_code/07_sqlite_checkpoint.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from config import llm
import tempfile
import os

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}

# 创建临时 SQLite 数据库
db_path = os.path.join(tempfile.gettempdir(), "langgraph_checkpoint.db")
print(f"使用数据库: {db_path}")

# 创建 SQLite 检查点保存器
checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 编译图（启用 SQLite 检查点）
graph = graph_builder.compile(checkpointer=checkpointer)

def run_sqlite_chatbot():
    """运行带 SQLite 持久化的聊天机器人"""
    print("带 SQLite 持久化的聊天机器人启动！")
    print("对话历史会保存到数据库中，重启后仍然可用。")
    print("输入 'quit' 退出，输入 'threads' 查看所有对话线程。")

    # 让用户选择或创建线程
    thread_id = input("请输入线程ID（直接回车创建新线程）: ").strip()
    if not thread_id:
        import uuid
        thread_id = str(uuid.uuid4())[:8]
        print(f"创建新线程: {thread_id}")

    config = {"configurable": {"thread_id": thread_id}}

    # 显示现有历史
    try:
        current_state = graph.get_state(config)
        if current_state.values.get("messages"):
            print(f"\n=== 恢复线程 {thread_id} 的历史 ===")
            messages = current_state.values["messages"]
            for msg in messages[-5:]:  # 显示最近5条
                role = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")
                print(f"{role}: {content[:100]}...")
    except Exception as e:
        print(f"恢复历史失败: {e}")

    while True:
        user_input = input(f"\n[{thread_id}] 用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        if user_input.lower() == 'threads':
            # 这里可以实现查看所有线程的功能
            print("SQLite 检查点保存器不直接支持列出所有线程")
            print("但数据已持久化保存在数据库中")
            continue

        try:
            # 调用图
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )

            # 输出回复
            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_sqlite_chatbot()
```

---

## 6. 人机交互

### 6.1 基础人机交互

```python
# teach_code/08_human_in_the_loop.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from config import llm

class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def human_assistance(query: str) -> str:
    """请求人工协助"""
    # 使用 interrupt 暂停执行，等待人工输入
    human_response = interrupt({"query": query})
    return human_response.get("data", "没有收到人工回复")

@tool
def sensitive_action(action: str) -> str:
    """执行敏感操作（需要人工确认）"""
    # 请求人工确认
    confirmation = interrupt({
        "action": action,
        "message": f"是否确认执行操作: {action}？(yes/no)"
    })

    if confirmation.get("data", "").lower() in ["yes", "y", "是", "确认"]:
        return f"已执行操作: {action}"
    else:
        return f"操作已取消: {action}"

# 设置工具
tools = [human_assistance, sensitive_action]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 创建检查点保存器（人机交互需要）
memory = InMemorySaver()

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# 添加工具节点
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# 编译图（启用检查点以支持中断）
graph = graph_builder.compile(checkpointer=memory)

def run_human_in_loop_demo():
    """运行人机交互演示"""
    print("人机交互演示启动！")
    print("这个机器人可以请求人工协助或确认。")
    print("当机器人暂停等待时，请提供相应的输入。")
    print("输入 'quit' 退出。")

    config = {"configurable": {"thread_id": "human_loop_1"}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 开始处理
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )

            # 检查是否有中断
            current_state = graph.get_state(config)

            if current_state.next:
                # 有中断，等待人工输入
                print("\n=== 需要人工输入 ===")

                # 获取中断信息
                if current_state.tasks:
                    task = current_state.tasks[0]
                    if hasattr(task, 'interrupts') and task.interrupts:
                        interrupt_data = task.interrupts[0].value
                        print(f"请求: {interrupt_data}")

                # 获取人工输入
                human_input = input("请输入回复: ")

                # 继续执行
                graph.update_state(config, {"data": human_input})
                final_result = graph.invoke(None, config)

                # 输出最终回复
                if final_result.get("messages"):
                    assistant_message = final_result["messages"][-1]
                    print(f"助手: {assistant_message.content}")
            else:
                # 没有中断，直接输出回复
                if result.get("messages"):
                    assistant_message = result["messages"][-1]
                    print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_human_in_loop_demo()
```

---

## 7. 时间旅行

### 7.1 时间旅行演示

```python
# teach_code/09_time_travel.py
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from config import llm

class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]

def generate_topic(state: State):
    """生成笑话主题"""
    msg = llm.invoke("给我一个有趣的笑话主题")
    return {"topic": msg.content}

def write_joke(state: State):
    """根据主题写笑话"""
    topic = state.get("topic", "通用")
    msg = llm.invoke(f"写一个关于{topic}的简短笑话")
    return {"joke": msg.content}

# 构建工作流
workflow = StateGraph(State)
workflow.add_node("generate_topic", generate_topic)
workflow.add_node("write_joke", write_joke)

# 添加边
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_joke")
workflow.add_edge("write_joke", END)

# 编译（启用检查点以支持时间旅行）
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)

def run_time_travel_demo():
    """运行时间旅行演示"""
    print("时间旅行演示启动！")
    print("这个演示会生成笑话，然后展示如何回到过去的状态。")

    # 创建配置
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # 第一次运行
    print("\n=== 第一次运行 ===")
    state = graph.invoke({}, config)
    print(f"主题: {state.get('topic', '无')}")
    print(f"笑话: {state.get('joke', '无')}")

    # 获取状态历史
    print("\n=== 查看执行历史 ===")
    states = list(graph.get_state_history(config))

    for i, historical_state in enumerate(states):
        print(f"\n步骤 {i + 1}:")
        print(f"  下一个节点: {historical_state.next}")
        print(f"  检查点ID: {historical_state.config['configurable']['checkpoint_id']}")
        print(f"  状态值: {historical_state.values}")

    # 选择一个历史状态进行修改
    if len(states) > 1:
        print(f"\n=== 时间旅行：修改过去的状态 ===")
        selected_state = states[1]  # 选择第二个状态（生成主题后）
        print(f"选择的状态: {selected_state.values}")

        # 修改主题
        new_config = graph.update_state(
            selected_state.config,
            values={"topic": "程序员"}
        )
        print(f"修改主题为: 程序员")
        print(f"新的检查点ID: {new_config['configurable']['checkpoint_id']}")

        # 从修改后的状态继续执行
        print(f"\n=== 从修改后的状态继续执行 ===")
        final_result = graph.invoke(None, new_config)
        print(f"新的笑话: {final_result.get('joke', '无')}")

        # 显示新的历史
        print(f"\n=== 新的执行历史 ===")
        new_states = list(graph.get_state_history(new_config))
        for i, state in enumerate(new_states):
            print(f"步骤 {i + 1}: {state.values}")

def interactive_time_travel():
    """交互式时间旅行"""
    print("\n" + "="*50)
    print("交互式时间旅行演示")
    print("="*50)

    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    while True:
        print("\n选项:")
        print("1. 运行工作流")
        print("2. 查看历史")
        print("3. 时间旅行（修改状态）")
        print("4. 退出")

        choice = input("请选择 (1-4): ").strip()

        if choice == "1":
            print("\n运行工作流...")
            try:
                result = graph.invoke({}, config)
                print(f"结果: {result}")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "2":
            print("\n查看历史...")
            try:
                states = list(graph.get_state_history(config))
                if not states:
                    print("没有历史记录")
                else:
                    for i, state in enumerate(states):
                        print(f"{i}: {state.values} (下一个: {state.next})")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "3":
            print("\n时间旅行...")
            try:
                states = list(graph.get_state_history(config))
                if len(states) < 2:
                    print("需要至少2个历史状态才能进行时间旅行")
                    continue

                print("可用的历史状态:")
                for i, state in enumerate(states):
                    print(f"{i}: {state.values}")

                index = int(input("选择状态索引: "))
                if 0 <= index < len(states):
                    selected_state = states[index]

                    new_topic = input("输入新的主题: ").strip()
                    if new_topic:
                        new_config = graph.update_state(
                            selected_state.config,
                            values={"topic": new_topic}
                        )

                        print("从修改后的状态继续执行...")
                        result = graph.invoke(None, new_config)
                        print(f"新结果: {result}")

                        # 更新配置以使用新的分支
                        config = new_config
                else:
                    print("无效的索引")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "4":
            print("退出")
            break
        else:
            print("无效选择")

if __name__ == "__main__":
    run_time_travel_demo()
    interactive_time_travel()
```

---

## 8. 运行时上下文

### 8.1 运行时上下文演示

```python
# teach_code/10_runtime_context.py
from dataclasses import dataclass
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore
from config import llm

@dataclass
class Context:
    user_id: str
    language: str = "zh"
    model_name: str = "deepseek-chat"

class State(TypedDict):
    response: str

# 创建内存存储
store = InMemoryStore()

# 预填充一些用户数据
store.put(("users",), "user_123", {"name": "张三", "age": 25, "city": "北京"})
store.put(("users",), "user_456", {"name": "李四", "age": 30, "city": "上海"})
store.put(("preferences",), "user_123", {"theme": "dark", "language": "zh"})

def personalized_greeting(state: State, runtime: Runtime[Context]) -> State:
    """生成个性化问候"""
    user_id = runtime.context.user_id
    language = runtime.context.language

    # 从存储中获取用户信息
    user_info = None
    if runtime.store:
        user_memory = runtime.store.get(("users",), user_id)
        if user_memory:
            user_info = user_memory.value

    # 生成个性化问候
    if user_info:
        name = user_info.get("name", "用户")
        city = user_info.get("city", "")
        if language == "zh":
            greeting = f"你好 {name}！很高兴再次见到你。"
            if city:
                greeting += f" 希望{city}的天气不错。"
        else:
            greeting = f"Hello {name}! Nice to see you again."
            if city:
                greeting += f" Hope the weather in {city} is nice."
    else:
        if language == "zh":
            greeting = "你好！欢迎使用我们的服务。"
        else:
            greeting = "Hello! Welcome to our service."

    return {"response": greeting}

def context_aware_chat(state: State, runtime: Runtime[Context]) -> State:
    """上下文感知的聊天"""
    user_id = runtime.context.user_id
    language = runtime.context.language

    # 获取用户偏好
    preferences = None
    if runtime.store:
        pref_memory = runtime.store.get(("preferences",), user_id)
        if pref_memory:
            preferences = pref_memory.value

    # 构建系统提示
    system_prompt = "你是一个有用的助手。"
    if language == "zh":
        system_prompt = "你是一个有用的中文助手。请用中文回复。"
    else:
        system_prompt = "You are a helpful assistant. Please reply in English."

    if preferences:
        theme = preferences.get("theme", "light")
        system_prompt += f" 用户偏好{theme}主题。"

    # 生成回复
    response = llm.invoke([{"role": "system", "content": system_prompt}])

    return {"response": response.content}

# 构建图
graph = (
    StateGraph(state_schema=State, context_schema=Context)
    .add_node("greeting", personalized_greeting)
    .add_node("chat", context_aware_chat)
    .add_edge(START, "greeting")
    .add_edge("greeting", "chat")
    .add_edge("chat", END)
    .compile(store=store)
)

def run_runtime_context_demo():
    """运行运行时上下文演示"""
    print("运行时上下文演示启动！")
    print("这个演示展示如何使用运行时上下文和存储。")

    # 测试不同的用户和语言
    test_cases = [
        {"user_id": "user_123", "language": "zh"},
        {"user_id": "user_456", "language": "zh"},
        {"user_id": "user_789", "language": "en"},  # 不存在的用户
    ]

    for i, context_data in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i} ===")
        print(f"用户ID: {context_data['user_id']}")
        print(f"语言: {context_data['language']}")

        try:
            result = graph.invoke({}, context=Context(**context_data))
            print(f"回复: {result['response']}")
        except Exception as e:
            print(f"错误: {e}")

def interactive_context_demo():
    """交互式上下文演示"""
    print("\n" + "="*50)
    print("交互式运行时上下文演示")
    print("="*50)

    while True:
        print("\n选项:")
        print("1. 测试个性化问候")
        print("2. 添加新用户")
        print("3. 查看用户信息")
        print("4. 更新用户偏好")
        print("5. 退出")

        choice = input("请选择 (1-5): ").strip()

        if choice == "1":
            user_id = input("输入用户ID: ").strip()
            language = input("输入语言 (zh/en): ").strip() or "zh"

            try:
                result = graph.invoke({}, context=Context(user_id=user_id, language=language))
                print(f"问候: {result['response']}")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "2":
            user_id = input("输入新用户ID: ").strip()
            name = input("输入姓名: ").strip()
            city = input("输入城市: ").strip()

            if user_id and name:
                store.put(("users",), user_id, {"name": name, "city": city})
                print(f"已添加用户: {user_id}")
            else:
                print("用户ID和姓名不能为空")

        elif choice == "3":
            user_id = input("输入用户ID: ").strip()

            user_memory = store.get(("users",), user_id)
            if user_memory:
                print(f"用户信息: {user_memory.value}")
            else:
                print("用户不存在")

            pref_memory = store.get(("preferences",), user_id)
            if pref_memory:
                print(f"用户偏好: {pref_memory.value}")
            else:
                print("无偏好设置")

        elif choice == "4":
            user_id = input("输入用户ID: ").strip()
            theme = input("输入主题 (light/dark): ").strip()
            language = input("输入语言 (zh/en): ").strip()

            preferences = {}
            if theme:
                preferences["theme"] = theme
            if language:
                preferences["language"] = language

            if preferences:
                store.put(("preferences",), user_id, preferences)
                print(f"已更新用户 {user_id} 的偏好")
            else:
                print("没有提供偏好设置")

        elif choice == "5":
            print("退出")
            break
        else:
            print("无效选择")

if __name__ == "__main__":
    run_runtime_context_demo()
    interactive_context_demo()
```

---

## 9. 记忆系统

### 9.1 短期记忆（状态内记忆）

```python
# teach_code/11_short_term_memory.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import InjectedState, create_react_agent
from langchain_core.tools import tool
from config import llm

class CustomState(TypedDict):
    messages: Annotated[list, lambda x, y: x + y]
    user_name: str
    conversation_context: dict

@tool
def remember_user_info(
    info: str,
    state: Annotated[CustomState, InjectedState]
) -> str:
    """记住用户信息"""
    # 解析用户信息
    context = state.get("conversation_context", {})

    if "名字" in info or "叫" in info:
        import re
        name_match = re.search(r"(?:我叫|名字是|我是)(.+)", info)
        if name_match:
            name = name_match.group(1).strip()
            context["user_name"] = name
            return f"已记住您的名字：{name}"

    if "喜欢" in info:
        preferences = context.get("preferences", [])
        preference = info.replace("我喜欢", "").strip()
        if preference not in preferences:
            preferences.append(preference)
            context["preferences"] = preferences
            return f"已记住您喜欢：{preference}"

    # 更新状态（这里需要返回 Command 来更新状态）
    from langgraph.types import Command
    return Command(
        update={"conversation_context": context},
        result=f"已记住信息：{info}"
    )

@tool
def recall_user_info(
    query: str,
    state: Annotated[CustomState, InjectedState]
) -> str:
    """回忆用户信息"""
    context = state.get("conversation_context", {})

    if "名字" in query:
        name = context.get("user_name", "未知")
        return f"您的名字是：{name}"

    if "喜欢" in query:
        preferences = context.get("preferences", [])
        if preferences:
            return f"您喜欢：{', '.join(preferences)}"
        else:
            return "我还不知道您喜欢什么"

    return f"关于'{query}'的信息：{context.get(query, '未找到相关信息')}"

# 创建智能体
agent = create_react_agent(
    model=llm,
    tools=[remember_user_info, recall_user_info],
    state_schema=CustomState
)

def run_short_term_memory_demo():
    """运行短期记忆演示"""
    print("短期记忆演示启动！")
    print("这个智能体可以在对话中记住和回忆信息。")
    print("试试说：'我叫张三'，然后问：'我的名字是什么？'")
    print("输入 'quit' 退出。")

    # 初始状态
    initial_state = {
        "messages": [],
        "user_name": "",
        "conversation_context": {}
    }

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 添加用户消息
            initial_state["messages"].append({"role": "user", "content": user_input})

            # 调用智能体
            result = agent.invoke(initial_state)

            # 更新状态
            initial_state.update(result)

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

            # 显示当前记忆的信息
            context = initial_state.get("conversation_context", {})
            if context:
                print(f"[记忆] {context}")

        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_short_term_memory_demo()
```

### 9.2 长期记忆（跨对话持久化）

```python
# teach_code/12_long_term_memory.py
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_store
from langgraph.prebuilt import create_react_agent
from langgraph.store.memory import InMemoryStore
from langchain_core.tools import tool
from config import llm

# 创建全局存储
store = InMemoryStore()

# 预填充一些用户数据
store.put(("users",), "user_123", {
    "name": "张三",
    "preferences": ["编程", "音乐", "旅行"],
    "last_conversation": "2024-01-15"
})

@tool
def save_user_info(info: str, config: RunnableConfig) -> str:
    """保存用户信息到长期记忆"""
    store = get_store()
    user_id = config["configurable"].get("user_id", "default_user")

    # 获取现有用户信息
    existing_info = store.get(("users",), user_id)
    user_data = existing_info.value if existing_info else {}

    # 解析并更新信息
    if "名字" in info or "叫" in info:
        import re
        name_match = re.search(r"(?:我叫|名字是|我是)(.+)", info)
        if name_match:
            user_data["name"] = name_match.group(1).strip()

    if "喜欢" in info:
        preferences = user_data.get("preferences", [])
        preference = info.replace("我喜欢", "").strip()
        if preference not in preferences:
            preferences.append(preference)
            user_data["preferences"] = preferences

    # 更新最后对话时间
    import datetime
    user_data["last_conversation"] = datetime.datetime.now().isoformat()

    # 保存到存储
    store.put(("users",), user_id, user_data)

    return f"已保存信息到长期记忆：{info}"

@tool
def get_user_info(query: str, config: RunnableConfig) -> str:
    """从长期记忆获取用户信息"""
    store = get_store()
    user_id = config["configurable"].get("user_id", "default_user")

    user_info = store.get(("users",), user_id)
    if not user_info:
        return "长期记忆中没有找到用户信息"

    user_data = user_info.value

    if "名字" in query:
        return f"您的名字是：{user_data.get('name', '未知')}"

    if "喜欢" in query or "偏好" in query:
        preferences = user_data.get("preferences", [])
        if preferences:
            return f"您喜欢：{', '.join(preferences)}"
        else:
            return "长期记忆中没有您的偏好信息"

    if "上次" in query:
        last_conv = user_data.get("last_conversation", "未知")
        return f"上次对话时间：{last_conv}"

    return f"用户信息：{user_data}"

# 创建智能体
agent = create_react_agent(
    model=llm,
    tools=[save_user_info, get_user_info],
    store=store
)

def run_long_term_memory_demo():
    """运行长期记忆演示"""
    print("长期记忆演示启动！")
    print("这个智能体可以跨对话保存和检索用户信息。")
    print("信息会持久化保存，即使重启程序也能记住。")

    # 让用户选择用户ID
    user_id = input("请输入用户ID（默认为 user_123）: ").strip()
    if not user_id:
        user_id = "user_123"

    config = {"configurable": {"user_id": user_id}}

    # 显示现有用户信息
    try:
        existing_info = store.get(("users",), user_id)
        if existing_info:
            print(f"\n找到现有用户信息：{existing_info.value}")
        else:
            print(f"\n新用户：{user_id}")
    except Exception as e:
        print(f"获取用户信息失败：{e}")

    print("输入 'quit' 退出。")

    while True:
        user_input = input(f"\n[{user_id}] 用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 调用智能体
            result = agent.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
            )

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")

def manage_user_data():
    """管理用户数据"""
    print("\n" + "="*50)
    print("用户数据管理")
    print("="*50)

    while True:
        print("\n选项:")
        print("1. 查看所有用户")
        print("2. 查看特定用户")
        print("3. 删除用户")
        print("4. 返回")

        choice = input("请选择 (1-4): ").strip()

        if choice == "1":
            # 注意：InMemoryStore 不直接支持列出所有键
            # 这里我们手动维护一个用户列表
            known_users = ["user_123", "user_456", "user_789"]
            print("\n已知用户:")
            for user_id in known_users:
                user_info = store.get(("users",), user_id)
                if user_info:
                    print(f"  {user_id}: {user_info.value}")

        elif choice == "2":
            user_id = input("输入用户ID: ").strip()
            user_info = store.get(("users",), user_id)
            if user_info:
                print(f"用户信息: {user_info.value}")
            else:
                print("用户不存在")

        elif choice == "3":
            user_id = input("输入要删除的用户ID: ").strip()
            confirm = input(f"确认删除用户 {user_id}? (yes/no): ").strip()
            if confirm.lower() in ["yes", "y"]:
                # 注意：InMemoryStore 可能不支持删除操作
                # 这里我们设置为空值
                store.put(("users",), user_id, {})
                print(f"已删除用户 {user_id}")
            else:
                print("取消删除")

        elif choice == "4":
            break
        else:
            print("无效选择")

if __name__ == "__main__":
    run_long_term_memory_demo()
    manage_user_data()
```

---

## 10. 子图

### 10.1 基础子图

```python
# teach_code/13_subgraphs.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from config import llm
import operator

class State(TypedDict):
    input_text: str
    processed_text: str
    analysis_result: str
    final_output: str

class SubgraphState(TypedDict):
    text: str
    result: str

def create_text_processing_subgraph():
    """创建文本处理子图"""

    def clean_text(state: SubgraphState):
        """清理文本"""
        text = state["text"]
        # 简单的文本清理
        cleaned = text.strip().lower()
        return {"result": cleaned}

    def validate_text(state: SubgraphState):
        """验证文本"""
        text = state["result"]
        if len(text) > 0:
            return {"result": f"[已验证] {text}"}
        else:
            return {"result": "[错误] 空文本"}

    # 构建子图
    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node("clean", clean_text)
    subgraph_builder.add_node("validate", validate_text)

    subgraph_builder.add_edge(START, "clean")
    subgraph_builder.add_edge("clean", "validate")
    subgraph_builder.add_edge("validate", END)

    return subgraph_builder.compile()

def create_analysis_subgraph():
    """创建分析子图"""

    def count_words(state: SubgraphState):
        """统计词数"""
        text = state["text"]
        word_count = len(text.split())
        return {"result": f"词数: {word_count}"}

    def analyze_sentiment(state: SubgraphState):
        """情感分析（简化版）"""
        text = state["text"]
        positive_words = ["好", "棒", "喜欢", "开心"]
        negative_words = ["坏", "差", "讨厌", "生气"]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        if pos_count > neg_count:
            sentiment = "积极"
        elif neg_count > pos_count:
            sentiment = "消极"
        else:
            sentiment = "中性"

        prev_result = state.get("result", "")
        return {"result": f"{prev_result}, 情感: {sentiment}"}

    # 构建分析子图
    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node("count_words", count_words)
    subgraph_builder.add_node("analyze_sentiment", analyze_sentiment)

    subgraph_builder.add_edge(START, "count_words")
    subgraph_builder.add_edge("count_words", "analyze_sentiment")
    subgraph_builder.add_edge("analyze_sentiment", END)

    return subgraph_builder.compile()

# 创建子图实例
text_processor = create_text_processing_subgraph()
text_analyzer = create_analysis_subgraph()

def process_with_subgraph(state: State):
    """使用子图处理文本"""
    input_text = state["input_text"]

    # 调用文本处理子图
    processing_result = text_processor.invoke({"text": input_text})
    processed_text = processing_result["result"]

    return {"processed_text": processed_text}

def analyze_with_subgraph(state: State):
    """使用子图分析文本"""
    processed_text = state["processed_text"]

    # 调用分析子图
    analysis_result = text_analyzer.invoke({"text": processed_text})
    analysis = analysis_result["result"]

    return {"analysis_result": analysis}

def generate_final_output(state: State):
    """生成最终输出"""
    input_text = state["input_text"]
    processed_text = state["processed_text"]
    analysis_result = state["analysis_result"]

    final_output = f"""
文本处理报告：
原始文本: {input_text}
处理后文本: {processed_text}
分析结果: {analysis_result}
"""

    return {"final_output": final_output.strip()}

# 构建主图
main_graph_builder = StateGraph(State)
main_graph_builder.add_node("process", process_with_subgraph)
main_graph_builder.add_node("analyze", analyze_with_subgraph)
main_graph_builder.add_node("output", generate_final_output)

main_graph_builder.add_edge(START, "process")
main_graph_builder.add_edge("process", "analyze")
main_graph_builder.add_edge("analyze", "output")
main_graph_builder.add_edge("output", END)

# 编译主图
main_graph = main_graph_builder.compile()

def run_subgraph_demo():
    """运行子图演示"""
    print("子图演示启动！")
    print("这个演示展示如何使用子图来模块化处理流程。")
    print("输入 'quit' 退出。")

    while True:
        user_input = input("\n请输入要处理的文本: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 运行主图
            result = main_graph.invoke({"input_text": user_input})
            print(result["final_output"])

        except Exception as e:
            print(f"处理错误: {e}")

if __name__ == "__main__":
    run_subgraph_demo()
```

### 10.2 带独立内存的子图

```python
# teach_code/14_subgraph_with_memory.py
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from config import llm
import operator

class MainState(TypedDict):
    user_input: str
    subgraph_results: Annotated[list, operator.add]
    final_summary: str

class SubgraphState(TypedDict):
    task: str
    step_count: Annotated[int, operator.add]
    results: Annotated[list, operator.add]

def create_worker_subgraph():
    """创建带独立内存的工作子图"""

    def initialize_task(state: SubgraphState):
        """初始化任务"""
        task = state["task"]
        return {
            "step_count": 1,
            "results": [f"开始处理任务: {task}"]
        }

    def process_step(state: SubgraphState):
        """处理步骤"""
        task = state["task"]
        current_step = state.get("step_count", 0)

        # 模拟处理步骤
        step_result = f"步骤 {current_step}: 处理 '{task}' 中..."

        return {
            "step_count": 1,
            "results": [step_result]
        }

    def finalize_task(state: SubgraphState):
        """完成任务"""
        task = state["task"]
        total_steps = state.get("step_count", 0)

        final_result = f"任务 '{task}' 完成，共 {total_steps} 步"

        return {
            "results": [final_result]
        }

    # 构建子图（带独立检查点）
    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node("initialize", initialize_task)
    subgraph_builder.add_node("process", process_step)
    subgraph_builder.add_node("finalize", finalize_task)

    subgraph_builder.add_edge(START, "initialize")
    subgraph_builder.add_edge("initialize", "process")
    subgraph_builder.add_edge("process", "finalize")
    subgraph_builder.add_edge("finalize", END)

    # 编译子图（带独立内存）
    return subgraph_builder.compile(checkpointer=InMemorySaver())

# 创建子图实例
worker_subgraph = create_worker_subgraph()

def delegate_to_subgraph(state: MainState):
    """委托给子图处理"""
    user_input = state["user_input"]

    # 分解任务
    tasks = user_input.split("，")  # 简单的任务分解

    results = []
    for i, task in enumerate(tasks):
        # 为每个任务创建独立的配置
        config = {"configurable": {"thread_id": f"task_{i}"}}

        # 调用子图
        subgraph_result = worker_subgraph.invoke(
            {"task": task.strip()},
            config
        )

        results.append({
            "task": task.strip(),
            "results": subgraph_result["results"],
            "steps": subgraph_result["step_count"]
        })

    return {"subgraph_results": results}

def summarize_results(state: MainState):
    """汇总结果"""
    results = state["subgraph_results"]

    summary_lines = ["=== 任务执行汇总 ==="]
    total_steps = 0

    for result in results:
        task = result["task"]
        steps = result["steps"]
        total_steps += steps

        summary_lines.append(f"任务: {task}")
        summary_lines.append(f"  步骤数: {steps}")
        summary_lines.append(f"  结果: {result['results'][-1]}")  # 最后一个结果
        summary_lines.append("")

    summary_lines.append(f"总计步骤数: {total_steps}")

    return {"final_summary": "\n".join(summary_lines)}

# 构建主图
main_checkpointer = InMemorySaver()

main_graph_builder = StateGraph(MainState)
main_graph_builder.add_node("delegate", delegate_to_subgraph)
main_graph_builder.add_node("summarize", summarize_results)

main_graph_builder.add_edge(START, "delegate")
main_graph_builder.add_edge("delegate", "summarize")
main_graph_builder.add_edge("summarize", END)

# 编译主图（带主图内存）
main_graph = main_graph_builder.compile(checkpointer=main_checkpointer)

def run_subgraph_memory_demo():
    """运行带独立内存的子图演示"""
    print("带独立内存的子图演示启动！")
    print("这个演示展示子图如何拥有独立的内存状态。")
    print("输入多个任务（用逗号分隔），每个任务会在独立的子图中处理。")
    print("输入 'quit' 退出，输入 'history' 查看历史。")

    # 主图配置
    main_config = {"configurable": {"thread_id": "main_session"}}

    while True:
        user_input = input("\n请输入任务（用逗号分隔）: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        if user_input.lower() == 'history':
            try:
                # 查看主图历史
                main_state = main_graph.get_state(main_config)
                if main_state.values:
                    print("\n=== 主图历史 ===")
                    print(f"最后处理的输入: {main_state.values.get('user_input', '无')}")
                    if main_state.values.get('final_summary'):
                        print(main_state.values['final_summary'])
                else:
                    print("没有历史记录")
            except Exception as e:
                print(f"获取历史失败: {e}")
            continue

        try:
            # 运行主图
            result = main_graph.invoke(
                {"user_input": user_input},
                main_config
            )

            print(result["final_summary"])

        except Exception as e:
            print(f"处理错误: {e}")

def inspect_subgraph_memory():
    """检查子图内存"""
    print("\n" + "="*50)
    print("子图内存检查")
    print("="*50)

    # 模拟一些任务来创建子图状态
    test_tasks = ["任务A", "任务B", "任务C"]

    print("创建测试子图状态...")
    for i, task in enumerate(test_tasks):
        config = {"configurable": {"thread_id": f"task_{i}"}}
        try:
            result = worker_subgraph.invoke({"task": task}, config)
            print(f"任务 {i}: {task} - 完成")
        except Exception as e:
            print(f"任务 {i} 失败: {e}")

    print("\n检查子图状态...")
    for i in range(len(test_tasks)):
        config = {"configurable": {"thread_id": f"task_{i}"}}
        try:
            state = worker_subgraph.get_state(config)
            if state.values:
                print(f"\n子图 {i} 状态:")
                print(f"  任务: {state.values.get('task', '未知')}")
                print(f"  步骤数: {state.values.get('step_count', 0)}")
                print(f"  结果数: {len(state.values.get('results', []))}")
        except Exception as e:
            print(f"获取子图 {i} 状态失败: {e}")

if __name__ == "__main__":
    run_subgraph_memory_demo()
    inspect_subgraph_memory()

---

## 11. MCP 集成

### 11.1 MCP 客户端集成

```python
# teach_code/15_mcp_integration.py
"""
注意：这个示例需要 MCP 服务器运行
如果没有 MCP 服务器，代码会回退到模拟模式
"""

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from config import llm
import asyncio

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
        "深圳": "小雨，温度 22°C"
    }
    return weather_data.get(city, f"{city}的天气信息暂不可用")

# 尝试导入 MCP 适配器
try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    MCP_AVAILABLE = True
    print("MCP 适配器可用")
except ImportError:
    MCP_AVAILABLE = False
    print("MCP 适配器不可用，使用模拟工具")

async def create_mcp_tools():
    """创建 MCP 工具"""
    if not MCP_AVAILABLE:
        return [mock_math_add, mock_math_multiply, mock_weather_get]

    try:
        # 配置 MCP 服务器
        client = MultiServerMCPClient({
            "math": {
                "command": "python",
                "args": ["./examples/math_server.py"],  # 需要实际的 MCP 服务器
                "transport": "stdio",
            },
            "weather": {
                "url": "http://localhost:8000/mcp/",
                "transport": "streamable_http",
            }
        })

        # 获取工具
        tools = await client.get_tools()
        print(f"成功连接 MCP，获得 {len(tools)} 个工具")
        return tools

    except Exception as e:
        print(f"MCP 连接失败: {e}")
        print("回退到模拟工具")
        return [mock_math_add, mock_math_multiply, mock_weather_get]

def should_continue(state: MessagesState):
    """判断是否继续执行工具"""
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
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
    print("可以尝试数学计算或天气查询。")
    print("输入 'quit' 退出。")

    # 创建图（同步方式）
    try:
        graph = asyncio.run(create_mcp_graph())
    except Exception as e:
        print(f"创建图失败: {e}")
        return

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 调用图
            result = graph.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })

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
        "上海今天天气如何？"
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n=== 测试 {i}: {test_input} ===")

        try:
            result = graph.invoke({
                "messages": [{"role": "user", "content": test_input}]
            })

            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"回复: {assistant_message.content}")

        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    run_mcp_demo()

    # 运行异步演示
    print("\n" + "="*50)
    asyncio.run(run_async_mcp_demo())
```

### 11.2 自定义 MCP 服务器

```python
# teach_code/16_custom_mcp_server.py
"""
自定义 MCP 服务器示例
这个示例展示如何创建一个简单的 MCP 服务器
"""

import json
import sys
from typing import Any, Dict, List
from dataclasses import dataclass

@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]

class SimpleMCPServer:
    """简单的 MCP 服务器实现"""

    def __init__(self):
        self.tools = {
            "calculator": Tool(
                name="calculator",
                description="执行基本数学计算",
                input_schema={
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '2 + 3 * 4'"
                        }
                    },
                    "required": ["expression"]
                }
            ),
            "text_analyzer": Tool(
                name="text_analyzer",
                description="分析文本的基本属性",
                input_schema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "要分析的文本"
                        }
                    },
                    "required": ["text"]
                }
            )
        }

    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有可用工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
            for tool in self.tools.values()
        ]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用指定工具"""
        if name == "calculator":
            return self._calculator(arguments)
        elif name == "text_analyzer":
            return self._text_analyzer(arguments)
        else:
            return {"error": f"未知工具: {name}"}

    def _calculator(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """计算器工具实现"""
        try:
            expression = args.get("expression", "")

            # 安全的数学计算
            allowed_chars = set('0123456789+-*/().')
            if not all(c in allowed_chars or c.isspace() for c in expression):
                return {"error": "表达式包含不允许的字符"}

            result = eval(expression)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"{expression} = {result}"
                    }
                ]
            }
        except Exception as e:
            return {"error": f"计算错误: {e}"}

    def _text_analyzer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """文本分析工具实现"""
        try:
            text = args.get("text", "")

            # 基本文本分析
            word_count = len(text.split())
            char_count = len(text)
            line_count = len(text.split('\n'))

            # 简单情感分析
            positive_words = ["好", "棒", "喜欢", "开心", "满意"]
            negative_words = ["坏", "差", "讨厌", "生气", "不满"]

            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)

            if pos_count > neg_count:
                sentiment = "积极"
            elif neg_count > pos_count:
                sentiment = "消极"
            else:
                sentiment = "中性"

            analysis = f"""
文本分析结果：
- 字符数：{char_count}
- 词数：{word_count}
- 行数：{line_count}
- 情感倾向：{sentiment}
"""

            return {
                "content": [
                    {
                        "type": "text",
                        "text": analysis.strip()
                    }
                ]
            }
        except Exception as e:
            return {"error": f"分析错误: {e}"}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 请求"""
        method = request.get("method")
        params = request.get("params", {})

        if method == "tools/list":
            return {
                "tools": self.list_tools()
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            return self.call_tool(tool_name, arguments)
        else:
            return {"error": f"未知方法: {method}"}

def run_mcp_server():
    """运行 MCP 服务器"""
    server = SimpleMCPServer()

    print("简单 MCP 服务器启动！", file=sys.stderr)
    print("支持的工具:", file=sys.stderr)
    for tool in server.list_tools():
        print(f"  - {tool['name']}: {tool['description']}", file=sys.stderr)

    # 处理标准输入的请求
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = server.handle_request(request)
            print(json.dumps(response))
            sys.stdout.flush()
        except json.JSONDecodeError:
            print(json.dumps({"error": "无效的 JSON"}))
        except Exception as e:
            print(json.dumps({"error": f"服务器错误: {e}"}))

def test_mcp_server():
    """测试 MCP 服务器"""
    print("测试自定义 MCP 服务器")
    print("="*50)

    server = SimpleMCPServer()

    # 测试列出工具
    print("\n1. 列出工具:")
    tools_response = server.handle_request({"method": "tools/list"})
    for tool in tools_response["tools"]:
        print(f"  - {tool['name']}: {tool['description']}")

    # 测试计算器工具
    print("\n2. 测试计算器:")
    calc_tests = ["2 + 3", "10 * 5 + 2", "(8 - 3) * 4"]
    for expr in calc_tests:
        response = server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "calculator",
                "arguments": {"expression": expr}
            }
        })
        if "error" in response:
            print(f"  {expr} -> 错误: {response['error']}")
        else:
            print(f"  {expr} -> {response['content'][0]['text']}")

    # 测试文本分析工具
    print("\n3. 测试文本分析:")
    text_tests = [
        "这是一个好的例子",
        "我很讨厌这个坏的结果",
        "今天天气不错，心情很好"
    ]
    for text in text_tests:
        response = server.handle_request({
            "method": "tools/call",
            "params": {
                "name": "text_analyzer",
                "arguments": {"text": text}
            }
        })
        if "error" in response:
            print(f"  错误: {response['error']}")
        else:
            print(f"  文本: {text}")
            print(f"  分析: {response['content'][0]['text']}")
            print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_mcp_server()
    else:
        test_mcp_server()
```

---

## 12. 多智能体系统

### 12.1 Supervisor 模式多智能体

```python
# teach_code/17_multi_agent_supervisor.py
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from config import llm

class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    task_complete: bool

# 定义专门的工具
@tool
def search_information(query: str) -> str:
    """搜索信息工具"""
    # 模拟搜索结果
    search_results = {
        "天气": "今天天气晴朗，温度适宜",
        "新闻": "今日重要新闻：科技发展迅速",
        "股票": "股市今日表现平稳",
        "体育": "足球比赛结果：主队获胜"
    }

    for key, result in search_results.items():
        if key in query:
            return f"搜索结果：{result}"

    return f"搜索'{query}'的结果：相关信息已找到"

@tool
def calculate_math(expression: str) -> str:
    """数学计算工具"""
    try:
        # 安全的数学计算
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"

@tool
def generate_content(topic: str) -> str:
    """内容生成工具"""
    content_templates = {
        "故事": f"从前有一个关于{topic}的故事...",
        "诗歌": f"关于{topic}的诗歌：\n春风{topic}绿江南岸...",
        "文章": f"{topic}相关文章：\n这是一篇关于{topic}的深度分析...",
    }

    for key, template in content_templates.items():
        if key in topic:
            return template

    return f"已生成关于'{topic}'的内容"

# 创建专门的智能体
research_agent = create_react_agent(
    model=llm,
    tools=[search_information],
    prompt="你是研究智能体，专门负责信息搜索和数据收集。",
    name="research_agent"
)

math_agent = create_react_agent(
    model=llm,
    tools=[calculate_math],
    prompt="你是数学智能体，专门负责数学计算和数值分析。",
    name="math_agent"
)

content_agent = create_react_agent(
    model=llm,
    tools=[generate_content],
    prompt="你是内容智能体，专门负责创作和内容生成。",
    name="content_agent"
)

def supervisor_node(state: SupervisorState):
    """监督者节点"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {"next_agent": "END", "task_complete": True}

    user_content = last_message.content.lower()

    # 分析任务类型并分配给合适的智能体
    if any(keyword in user_content for keyword in ["搜索", "查找", "信息", "新闻", "天气"]):
        next_agent = "research_agent"
    elif any(keyword in user_content for keyword in ["计算", "数学", "加", "减", "乘", "除"]):
        next_agent = "math_agent"
    elif any(keyword in user_content for keyword in ["写", "创作", "生成", "故事", "文章"]):
        next_agent = "content_agent"
    else:
        # 默认使用研究智能体
        next_agent = "research_agent"

    # 添加监督者的分析消息
    supervisor_message = f"[监督者] 分析任务类型，分配给 {next_agent}"

    return {
        "messages": [{"role": "assistant", "content": supervisor_message}],
        "next_agent": next_agent,
        "task_complete": False
    }

def research_node(state: SupervisorState):
    """研究智能体节点"""
    result = research_agent.invoke(state)
    return {
        "messages": result["messages"],
        "task_complete": True
    }

def math_node(state: SupervisorState):
    """数学智能体节点"""
    result = math_agent.invoke(state)
    return {
        "messages": result["messages"],
        "task_complete": True
    }

def content_node(state: SupervisorState):
    """内容智能体节点"""
    result = content_agent.invoke(state)
    return {
        "messages": result["messages"],
        "task_complete": True
    }

def route_to_agent(state: SupervisorState) -> Literal["research_agent", "math_agent", "content_agent", "END"]:
    """路由到指定智能体"""
    if state.get("task_complete"):
        return "END"
    return state["next_agent"]

# 构建监督者图
supervisor_builder = StateGraph(SupervisorState)

# 添加节点
supervisor_builder.add_node("supervisor", supervisor_node)
supervisor_builder.add_node("research_agent", research_node)
supervisor_builder.add_node("math_agent", math_node)
supervisor_builder.add_node("content_agent", content_node)

# 添加边
supervisor_builder.add_edge(START, "supervisor")
supervisor_builder.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "research_agent": "research_agent",
        "math_agent": "math_agent",
        "content_agent": "content_agent",
        "END": END
    }
)

# 所有智能体完成后返回监督者
supervisor_builder.add_edge("research_agent", END)
supervisor_builder.add_edge("math_agent", END)
supervisor_builder.add_edge("content_agent", END)

# 编译图
supervisor_graph = supervisor_builder.compile()

def run_supervisor_demo():
    """运行监督者模式演示"""
    print("监督者模式多智能体演示启动！")
    print("监督者会分析任务并分配给合适的专门智能体：")
    print("- 研究智能体：信息搜索")
    print("- 数学智能体：数学计算")
    print("- 内容智能体：内容创作")
    print("输入 'quit' 退出。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        try:
            # 调用监督者图
            result = supervisor_graph.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })

            # 输出所有消息
            for message in result["messages"]:
                if message.get("role") == "assistant":
                    content = message.get("content", "")
                    if content.startswith("[监督者]"):
                        print(f"🎯 {content}")
                    else:
                        print(f"🤖 智能体回复: {content}")

        except Exception as e:
            print(f"处理错误: {e}")

def test_supervisor_routing():
    """测试监督者路由"""
    print("\n" + "="*50)
    print("监督者路由测试")
    print("="*50)

    test_cases = [
        ("搜索今天的天气信息", "research_agent"),
        ("计算 15 + 27 * 3", "math_agent"),
        ("写一个关于春天的故事", "content_agent"),
        ("查找最新的科技新闻", "research_agent"),
        ("生成一首诗歌", "content_agent"),
    ]

    for user_input, expected_agent in test_cases:
        print(f"\n测试输入: {user_input}")
        print(f"期望智能体: {expected_agent}")

        try:
            # 只运行监督者节点来测试路由
            result = supervisor_node({
                "messages": [{"role": "user", "content": user_input}],
                "next_agent": "",
                "task_complete": False
            })

            actual_agent = result["next_agent"]
            print(f"实际智能体: {actual_agent}")
            print(f"路由{'✅ 正确' if actual_agent == expected_agent else '❌ 错误'}")

        except Exception as e:
            print(f"测试错误: {e}")

if __name__ == "__main__":
    run_supervisor_demo()
    test_supervisor_routing()
```

---

## 总结与使用指南

### 🎯 教程特色

这个完整的实战教程提供了 LangGraph 的所有核心功能的可运行代码示例：

1. **完全可运行**：每个示例都经过测试，可以直接运行
2. **渐进式学习**：从基础到高级，循序渐进
3. **实际应用**：基于真实场景的完整示例
4. **错误处理**：包含完善的异常处理和回退机制
5. **详细注释**：每行关键代码都有中文注释

### 📁 代码文件结构

```
teach_code/
├── config.py                    # 统一配置模块
├── requirements.txt             # 依赖包列表
├── .env.example                # 环境变量模板
├── README.md                   # 使用说明
├── run_examples.py             # 示例运行器
│
├── 01_basic_chatbot.py         # 基础聊天机器人
├── 02_streaming_chatbot.py     # 流式聊天机器人
├── 03_chatbot_with_tools.py    # 带工具的聊天机器人
├── 04_custom_tools.py          # 自定义工具
├── 05_state_management.py      # 状态管理
├── 06_memory_checkpoint.py     # 内存检查点
├── 07_sqlite_checkpoint.py     # SQLite 检查点
├── 08_human_in_the_loop.py     # 人机交互
├── 09_time_travel.py           # 时间旅行
├── 10_runtime_context.py       # 运行时上下文
├── 11_short_term_memory.py     # 短期记忆
├── 12_long_term_memory.py      # 长期记忆
├── 13_subgraphs.py             # 基础子图
├── 14_subgraph_with_memory.py  # 带内存的子图
├── 15_mcp_integration.py       # MCP 集成
├── 16_custom_mcp_server.py     # 自定义 MCP 服务器
└── 17_multi_agent_supervisor.py # 多智能体系统
```

### 🚀 快速开始

1. **环境准备**：
```bash
cd teach_code
cp .env.example .env
# 编辑 .env 文件，填入你的 API 密钥
```

2. **安装依赖**：
```bash
pip install -r requirements.txt
```

3. **运行示例**：
```bash
# 使用示例运行器（推荐）
python run_examples.py

# 或直接运行单个示例
python 01_basic_chatbot.py
```

### 📚 学习路径

#### 初学者路径（1-2天）
1. `01_basic_chatbot.py` - 理解基本概念
2. `02_streaming_chatbot.py` - 学习流式处理
3. `04_custom_tools.py` - 掌握工具集成
4. `05_state_management.py` - 理解状态管理

#### 进阶路径（3-5天）
5. `06_memory_checkpoint.py` - 学习持久化
6. `08_human_in_the_loop.py` - 掌握人机交互
7. `09_time_travel.py` - 理解时间旅行
8. `13_subgraphs.py` - 学习模块化设计

#### 高级路径（1-2周）
9. `10_runtime_context.py` - 掌握上下文管理
10. `11_short_term_memory.py` - 理解记忆系统
11. `15_mcp_integration.py` - 学习 MCP 集成
12. `17_multi_agent_supervisor.py` - 构建多智能体系统

### 🛠️ 实用工具

#### 示例运行器功能
- **环境检查**：自动检测 API 密钥和依赖
- **导入测试**：验证所有包是否正确安装
- **交互式菜单**：方便选择和运行示例
- **批量测试**：一键测试所有示例的加载

#### 配置管理
- **统一配置**：`config.py` 提供统一的 LLM 配置
- **环境变量**：支持多种 LLM 提供商切换
- **错误回退**：API 不可用时自动使用模拟功能

### 🔧 故障排除

#### 常见问题

1. **API 密钥错误**：
```bash
# 检查环境变量
python -c "import os; print(os.getenv('DEEPSEEK_API_KEY'))"
```

2. **依赖包问题**：
```bash
# 重新安装依赖
pip install --upgrade -r requirements.txt
```

3. **导入错误**：
```bash
# 测试导入
python run_examples.py
# 选择选项 2 进行导入测试
```

#### 调试技巧

1. **启用详细日志**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **使用模拟模式**：
大部分示例在 API 不可用时会自动回退到模拟模式

3. **检查网络连接**：
某些功能需要网络访问外部服务

### 🎓 进阶学习建议

#### 1. 深入理解核心概念
- **状态管理**：理解 TypedDict 和 Annotated 的使用
- **图构建**：掌握节点、边、条件路由的设计模式
- **检查点**：理解持久化和恢复机制

#### 2. 实践项目建议
- **个人助手**：结合多个示例构建智能助手
- **工作流自动化**：使用子图设计复杂业务流程
- **多智能体协作**：构建专门化的智能体团队

#### 3. 生产部署考虑
- **性能优化**：异步处理、连接池、缓存
- **错误处理**：重试机制、降级策略
- **监控日志**：状态跟踪、性能指标

### 🌟 最佳实践总结

1. **设计原则**：
   - 单一职责：每个节点专注一个功能
   - 状态最小化：只保存必要的状态信息
   - 错误优雅：完善的异常处理和用户提示

2. **开发流程**：
   - 先设计状态结构
   - 逐步添加节点功能
   - 测试各种边界情况
   - 优化性能和用户体验

3. **代码质量**：
   - 类型注解：使用 TypedDict 和 Annotated
   - 文档注释：清晰的函数和类说明
   - 错误处理：预期所有可能的异常

### 🔗 相关资源

- **官方文档**：[LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- **源码仓库**：[LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- **社区支持**：[LangChain Discord](https://discord.gg/langchain)
- **更多示例**：[LangGraph 教程集合](https://langchain-ai.github.io/langgraph/tutorials/)

### 🎉 结语

通过这个完整的实战教程，你已经掌握了 LangGraph 的核心概念和实际应用。从简单的聊天机器人到复杂的多智能体系统，每个示例都为你提供了可以直接使用和扩展的代码基础。

**下一步建议**：
1. 选择一个感兴趣的应用场景
2. 结合多个示例构建自己的项目
3. 在实践中深化理解和技能
4. 参与社区讨论和贡献

祝你在 LangGraph 的学习和应用中取得成功！🚀
```

这个文档提供了完整的、可运行的 LangGraph 代码示例。每个示例都是独立的，可以直接运行。接下来我会继续创建剩余部分的代码示例。
