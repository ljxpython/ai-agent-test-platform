import os
from typing import Annotated

from config import llm
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

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
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 流式处理
            for event in graph.stream(
                {"messages": [{"role": "user", "content": user_input}]}
            ):
                for value in event.values():
                    if "messages" in value:
                        message = value["messages"][-1]
                        if hasattr(message, "content") and message.content:
                            print(f"助手: {message.content}")
                        elif hasattr(message, "tool_calls") and message.tool_calls:
                            print("正在搜索信息...")
        except Exception as e:
            print(f"处理错误: {e}")


if __name__ == "__main__":
    run_tool_chatbot()
