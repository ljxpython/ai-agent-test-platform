import datetime
import random
from typing import Annotated

from config import llm
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict


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
        allowed_chars = set("0123456789+-*/().")
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
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            for event in graph.stream(
                {"messages": [{"role": "user", "content": user_input}]}
            ):
                for value in event.values():
                    if "messages" in value:
                        message = value["messages"][-1]
                        if hasattr(message, "content") and message.content:
                            print(f"助手: {message.content}")
                        elif hasattr(message, "tool_calls") and message.tool_calls:
                            print("正在使用工具...")
        except Exception as e:
            print(f"处理错误: {e}")


if __name__ == "__main__":
    run_custom_tools_chatbot()
