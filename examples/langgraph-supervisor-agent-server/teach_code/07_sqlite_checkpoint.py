import json
import os
import pickle
import sqlite3
import tempfile
from datetime import datetime
from typing import Annotated

from config import llm
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list, add_messages]


class SimpleSQLiteStorage:
    """简单的 SQLite 存储实现"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                thread_id TEXT,
                message_index INTEGER,
                role TEXT,
                content TEXT,
                timestamp TEXT,
                PRIMARY KEY (thread_id, message_index)
            )
        """
        )
        conn.commit()
        conn.close()

    def save_messages(self, thread_id: str, messages: list):
        """保存消息到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 清除该线程的旧消息
        cursor.execute("DELETE FROM conversations WHERE thread_id = ?", (thread_id,))

        # 保存新消息
        for i, msg in enumerate(messages):
            role = "human" if hasattr(msg, "type") and msg.type == "human" else "ai"
            content = msg.content if hasattr(msg, "content") else str(msg)
            timestamp = datetime.now().isoformat()

            cursor.execute(
                """
                INSERT INTO conversations (thread_id, message_index, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (thread_id, i, role, content, timestamp),
            )

        conn.commit()
        conn.close()

    def load_messages(self, thread_id: str) -> list:
        """从数据库加载消息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT role, content FROM conversations
            WHERE thread_id = ?
            ORDER BY message_index
        """,
            (thread_id,),
        )

        rows = cursor.fetchall()
        conn.close()

        messages = []
        for role, content in rows:
            messages.append(
                {"role": "user" if role == "human" else "assistant", "content": content}
            )

        return messages

    def list_threads(self) -> list:
        """列出所有对话线程"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT thread_id FROM conversations")
        threads = [row[0] for row in cursor.fetchall()]

        conn.close()
        return threads


def chatbot_with_storage(state: State):
    """带存储的聊天机器人节点"""
    global current_thread_id

    response = llm.invoke(state["messages"])
    new_messages = state["messages"] + [response]

    # 保存到 SQLite
    print(
        f"保存消息到数据库，线程ID: {current_thread_id}, 消息数量: {len(new_messages)}"
    )
    sqlite_storage.save_messages(current_thread_id, new_messages)

    return {"messages": [response]}


def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}


# 创建 SQLite 数据库和存储
# db_path = os.path.join(tempfile.gettempdir(), "langgraph_conversations.db")
db_path = os.path.join("./langgraph_conversations.db")
print(f"使用 SQLite 数据库: {db_path}")

# 创建 SQLite 存储
sqlite_storage = SimpleSQLiteStorage(db_path)

# 全局变量用于存储当前线程ID
current_thread_id = "default"

# 创建内存检查点保存器（用于图的状态管理）
checkpointer = InMemorySaver()

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot_with_storage)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 编译图（启用 SQLite 检查点）
graph = graph_builder.compile(checkpointer=checkpointer)


def run_sqlite_chatbot():
    """运行带 SQLite 持久化的聊天机器人"""
    global current_thread_id

    print("带 SQLite 持久化的聊天机器人启动！")
    print("对话历史会保存到数据库中，重启后仍然可用。")
    print("可用命令:")
    print("  - 'quit' 或 'exit': 退出程序")
    print("  - 'threads': 查看所有对话线程")
    print("  - 'history': 查看当前线程的对话历史")

    # 让用户选择或创建线程
    thread_id = input("请输入线程ID（直接回车创建新线程）: ").strip()
    if not thread_id:
        import uuid

        thread_id = str(uuid.uuid4())[:8]
        print(f"创建新线程: {thread_id}")

    # 设置全局线程ID
    current_thread_id = thread_id
    config = {"configurable": {"thread_id": thread_id}}

    # 显示现有历史
    try:
        current_state = graph.get_state(config)
        if current_state.values.get("messages"):
            print(f"\n=== 恢复线程 {thread_id} 的历史 ===")
            messages = current_state.values["messages"]
            for msg in messages[-5:]:  # 显示最近5条
                role = (
                    "用户" if hasattr(msg, "type") and msg.type == "human" else "助手"
                )
                content = msg.content if hasattr(msg, "content") else str(msg)
                print(f"{role}: {content[:100]}...")
    except Exception as e:
        print(f"恢复历史失败: {e}")

    while True:
        user_input = input(f"\n[{thread_id}] 用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if user_input.lower() == "threads":
            # 显示所有保存的对话线程
            threads = sqlite_storage.list_threads()
            if threads:
                print(f"找到 {len(threads)} 个对话线程:")
                for i, tid in enumerate(threads, 1):
                    messages = sqlite_storage.load_messages(tid)
                    print(f"{i}. {tid} ({len(messages)} 条消息)")
            else:
                print("没有找到保存的对话线程")
            continue

        if user_input.lower().startswith("history"):
            # 显示当前线程的对话历史
            messages = sqlite_storage.load_messages(current_thread_id)
            if messages:
                print(f"\n=== 线程 {current_thread_id} 的对话历史 ===")
                for i, msg in enumerate(messages, 1):
                    role = "用户" if msg["role"] == "user" else "助手"
                    content = (
                        msg["content"][:200] + "..."
                        if len(msg["content"]) > 200
                        else msg["content"]
                    )
                    print(f"{i}. {role}: {content}")
            else:
                print(f"线程 {current_thread_id} 没有找到对话历史")
            continue

        try:
            # 调用图
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]}, config
            )

            # 输出回复
            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")


def demo_persistence():
    """演示持久化功能"""
    global current_thread_id

    print("\n" + "=" * 50)
    print("持久化功能演示")
    print("=" * 50)

    # 创建一个测试线程
    test_thread = "persistence_test"
    current_thread_id = test_thread
    config = {"configurable": {"thread_id": test_thread}}

    print(f"创建测试对话线程: {test_thread}")

    # 第一轮对话
    print("\n=== 第一轮对话 ===")
    result1 = graph.invoke(
        {"messages": [{"role": "user", "content": "我叫张三，我是一名程序员"}]}, config
    )
    print(f"助手: {result1['messages'][-1].content}")

    # 第二轮对话
    print("\n=== 第二轮对话 ===")
    result2 = graph.invoke(
        {"messages": [{"role": "user", "content": "我喜欢用 Python 编程"}]}, config
    )
    print(f"助手: {result2['messages'][-1].content}")

    # 模拟程序重启 - 重新创建图和检查点保存器
    print("\n=== 模拟程序重启 ===")
    print("注意：由于使用内存检查点，重启后数据会丢失")
    new_checkpointer = InMemorySaver()
    new_graph = graph_builder.compile(checkpointer=new_checkpointer)

    # 恢复对话
    print("\n=== 恢复对话 ===")
    result3 = new_graph.invoke(
        {"messages": [{"role": "user", "content": "你还记得我的名字和职业吗？"}]},
        config,
    )
    print(f"助手: {result3['messages'][-1].content}")

    # 显示完整历史
    print(f"\n=== 完整对话历史 ===")
    final_state = new_graph.get_state(config)
    for i, msg in enumerate(final_state.values["messages"], 1):
        role = "用户" if msg.get("role") == "user" else "助手"
        print(f"{i}. {role}: {msg.get('content', '')}")


def inspect_database():
    """检查数据库内容"""
    print("\n" + "=" * 50)
    print("数据库内容检查")
    print("=" * 50)

    try:
        import sqlite3

        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 查看表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"数据库表: {[table[0] for table in tables]}")

        # 查看检查点表的记录数
        if ("checkpoints",) in tables:
            cursor.execute("SELECT COUNT(*) FROM checkpoints;")
            count = cursor.fetchone()[0]
            print(f"检查点记录数: {count}")

            # 查看最近的几个检查点
            cursor.execute(
                """
                SELECT thread_id, checkpoint_id, created_at
                FROM checkpoints
                ORDER BY created_at DESC
                LIMIT 5
            """
            )
            recent_checkpoints = cursor.fetchall()
            print("\n最近的检查点:")
            for thread_id, checkpoint_id, created_at in recent_checkpoints:
                print(
                    f"  线程: {thread_id}, 检查点: {checkpoint_id[:8]}..., 时间: {created_at}"
                )

        conn.close()

    except Exception as e:
        print(f"检查数据库失败: {e}")


def cleanup_database():
    """清理数据库"""
    print("\n" + "=" * 50)
    print("数据库清理")
    print("=" * 50)

    try:
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"已删除数据库文件: {db_path}")
        else:
            print("数据库文件不存在")
    except Exception as e:
        print(f"清理数据库失败: {e}")


if __name__ == "__main__":
    try:
        run_sqlite_chatbot()
        demo_persistence()
        inspect_database()

        # 询问是否清理数据库
        cleanup = input("\n是否清理测试数据库? (y/N): ").strip().lower()
        if cleanup in ["y", "yes"]:
            cleanup_database()
        else:
            print(f"数据库保留在: {db_path}")

    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        print(f"程序错误: {e}")
