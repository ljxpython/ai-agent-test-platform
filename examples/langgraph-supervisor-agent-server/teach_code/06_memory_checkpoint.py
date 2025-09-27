from typing import Annotated

from config import llm
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


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
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if user_input.lower() == "history":
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
                {"messages": [{"role": "user", "content": user_input}]}, config
            )

            # 输出回复
            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")


def demo_multiple_threads():
    """演示多线程对话"""
    print("\n" + "=" * 50)
    print("多线程对话演示")
    print("=" * 50)

    # 创建两个不同的对话线程
    thread1_config = {"configurable": {"thread_id": "user_alice"}}
    thread2_config = {"configurable": {"thread_id": "user_bob"}}

    # 线程1的对话
    print("\n=== Alice 的对话 ===")
    graph.invoke(
        {"messages": [{"role": "user", "content": "我叫 Alice，我喜欢编程"}]},
        thread1_config,
    )

    # 线程2的对话
    print("\n=== Bob 的对话 ===")
    graph.invoke(
        {"messages": [{"role": "user", "content": "我叫 Bob，我喜欢音乐"}]},
        thread2_config,
    )

    # 继续线程1的对话
    print("\n=== Alice 继续对话 ===")
    result1 = graph.invoke(
        {"messages": [{"role": "user", "content": "你还记得我的名字和爱好吗？"}]},
        thread1_config,
    )
    print(f"回复: {result1['messages'][-1].content}")

    # 继续线程2的对话
    print("\n=== Bob 继续对话 ===")
    result2 = graph.invoke(
        {"messages": [{"role": "user", "content": "你还记得我的名字和爱好吗？"}]},
        thread2_config,
    )
    print(f"回复: {result2['messages'][-1].content}")

    # 显示两个线程的历史
    print("\n=== Alice 的完整历史 ===")
    alice_state = graph.get_state(thread1_config)
    for i, msg in enumerate(alice_state.values["messages"], 1):
        role = "用户" if hasattr(msg, "type") and msg.type == "human" else "助手"
        content = msg.content if hasattr(msg, "content") else str(msg)
        print(f"{i}. {role}: {content}")

    print("\n=== Bob 的完整历史 ===")
    bob_state = graph.get_state(thread2_config)
    for i, msg in enumerate(bob_state.values["messages"], 1):
        role = "用户" if hasattr(msg, "type") and msg.type == "human" else "助手"
        content = msg.content if hasattr(msg, "content") else str(msg)
        print(f"{i}. {role}: {content}")


def inspect_checkpointer():
    """检查检查点保存器的内部状态"""
    print("\n" + "=" * 50)
    print("检查点保存器状态检查")
    print("=" * 50)

    # 注意：InMemorySaver 不直接暴露内部存储
    # 但我们可以通过创建一些状态来演示

    test_configs = [
        {"configurable": {"thread_id": "test_1"}},
        {"configurable": {"thread_id": "test_2"}},
        {"configurable": {"thread_id": "test_3"}},
    ]

    # 为每个测试线程创建一些对话
    for i, config in enumerate(test_configs, 1):
        print(f"\n创建测试线程 {i}...")
        graph.invoke(
            {"messages": [{"role": "user", "content": f"这是测试线程 {i}"}]}, config
        )

        # 获取状态
        state = graph.get_state(config)
        print(f"线程 {i} 状态:")
        print(f"  消息数量: {len(state.values.get('messages', []))}")
        print(f"  检查点ID: {state.config['configurable']['checkpoint_id']}")


if __name__ == "__main__":
    # run_memory_chatbot()
    demo_multiple_threads()
    inspect_checkpointer()
