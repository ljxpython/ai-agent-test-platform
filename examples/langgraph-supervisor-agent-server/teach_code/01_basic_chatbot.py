from typing import Annotated

from config import llm
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


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
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        # 调用图
        result = graph.invoke({"messages": [{"role": "user", "content": user_input}]})

        # 输出回复
        assistant_message = result["messages"][-1]
        print(f"助手: {assistant_message.content}")


if __name__ == "__main__":
    run_chatbot()
