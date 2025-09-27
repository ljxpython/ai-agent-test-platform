#!/usr/bin/env python3
"""
02. 流式聊天机器人

这个示例展示了如何实现真正的流式输出，包括：
- LLM 响应的流式输出
- 实时显示生成的文本
- 更好的用户体验

运行方式：python 02_streaming_chatbot.py
"""

import sys
import time
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


def simulate_streaming_output(text: str, delay: float = 0.03):
    """模拟流式输出效果"""
    print("助手: ", end="", flush=True)
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()  # 换行


def stream_graph_updates(user_input: str):
    """流式处理图更新"""
    try:
        # 获取完整响应
        result = graph.invoke({"messages": [{"role": "user", "content": user_input}]})

        if "messages" in result and result["messages"]:
            response_text = result["messages"][-1].content
            # 模拟流式输出
            simulate_streaming_output(response_text)
        else:
            print("助手: 抱歉，我无法生成回复。")
    except Exception as e:
        print(f"助手: 抱歉，处理您的请求时出现错误：{e}")


def stream_with_real_llm_streaming(user_input: str):
    """使用真正的 LLM 流式输出（如果支持）"""
    try:
        # 尝试使用 LLM 的流式功能
        print("助手: ", end="", flush=True)

        # 直接调用 LLM 的流式方法
        for chunk in llm.stream([{"role": "user", "content": user_input}]):
            if hasattr(chunk, "content") and chunk.content:
                print(chunk.content, end="", flush=True)
        print()  # 换行

    except Exception as e:
        # 如果流式不可用，回退到模拟流式
        print(f"\n流式输出不可用，使用模拟流式: {e}")
        stream_graph_updates(user_input)


def run_streaming_chatbot():
    """运行流式聊天机器人"""
    print("🚀 流式聊天机器人启动！")
    print("这个机器人会实时显示生成的文本，提供更好的用户体验。")
    print("输入 'quit' 退出，输入 'mode' 切换流式模式。")

    use_real_streaming = True

    while True:
        user_input = input("\n用户: ")

        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break
        elif user_input.lower() == "mode":
            use_real_streaming = not use_real_streaming
            mode = "真实流式" if use_real_streaming else "模拟流式"
            print(f"已切换到 {mode} 模式")
            continue

        if use_real_streaming:
            stream_with_real_llm_streaming(user_input)
        else:
            stream_graph_updates(user_input)


def demo_streaming():
    """演示流式功能"""
    print("=== 流式输出演示 ===")

    test_messages = ["你好！", "请介绍一下流式输出的优势", "谢谢你的解释"]

    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 演示 {i} ---")
        print(f"用户: {message}")
        stream_with_real_llm_streaming(message)
        time.sleep(1)  # 短暂暂停


if __name__ == "__main__":
    # 可以选择运行演示或交互式聊天
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_streaming()
    else:
        run_streaming_chatbot()
