#!/usr/bin/env python3
"""
12. 长期记忆 (修复版本)

这个示例展示了如何实现长期记忆功能，避免序列化问题
"""

from typing import Annotated

from config import llm
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore
from typing_extensions import TypedDict

# 创建全局存储
store = InMemoryStore()

# 预填充一些示例数据
store.put(
    ("users",),
    "user_123",
    {
        "name": "张三",
        "preferences": ["编程", "音乐", "旅行"],
        "last_conversation": "2024-01-15",
    },
)

# 全局存储引用（避免序列化问题）
_global_store = store


@tool
def save_user_info(info: str) -> str:
    """保存用户信息到长期记忆"""
    user_id = "default_user"

    # 获取现有用户信息
    existing_info = _global_store.get(("users",), user_id)
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
    _global_store.put(("users",), user_id, user_data)

    return f"已保存信息到长期记忆：{info}"


@tool
def get_user_info(query: str) -> str:
    """从长期记忆获取用户信息"""
    user_id = "default_user"

    user_info = _global_store.get(("users",), user_id)
    if not user_info:
        return "长期记忆中没有找到用户信息"

    user_data = user_info.value

    if "名字" in query:
        return f"用户名字: {user_data.get('name', '未知')}"
    elif "喜欢" in query or "偏好" in query:
        preferences = user_data.get("preferences", [])
        return f"用户偏好: {', '.join(preferences) if preferences else '无'}"
    else:
        return f"用户信息: {user_data}"


# 状态定义
class State(TypedDict):
    messages: Annotated[list, add_messages]


# 创建工具列表
tools = [save_user_info, get_user_info]

# 绑定工具到 LLM
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 导入工具节点和条件
from langgraph.prebuilt import ToolNode, tools_condition

# 创建工具节点
tool_node = ToolNode(tools)

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# 添加条件边：如果 LLM 调用工具，则执行工具；否则结束
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")  # 工具执行后回到聊天机器人
graph_builder.add_edge(START, "chatbot")

# 编译图
graph = graph_builder.compile()


def run_demo():
    """运行演示"""
    print("长期记忆演示启动！")
    print("这个智能体可以记住用户信息并在后续对话中使用。")

    test_messages = ["我叫李四，我喜欢编程", "我的名字是什么？", "我喜欢什么？"]

    # 保持对话历史
    conversation_messages = []

    for i, message in enumerate(test_messages, 1):
        print(f"\n=== 测试 {i} ===")
        print(f"用户: {message}")

        try:
            # 添加用户消息到对话历史
            conversation_messages.append({"role": "user", "content": message})

            # 调用图，传入完整的对话历史
            result = graph.invoke({"messages": conversation_messages})

            # 获取最新的助手回复
            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

            # 将助手回复添加到对话历史
            conversation_messages.append(
                {"role": "assistant", "content": assistant_message.content}
            )

        except Exception as e:
            print(f"处理错误: {e}")


if __name__ == "__main__":
    run_demo()
