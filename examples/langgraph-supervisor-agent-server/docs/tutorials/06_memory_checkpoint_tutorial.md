# 06. 内存检查点教学

## 🎯 学习目标

通过这个教程，你将学会：
- 什么是检查点及其重要性
- 如何使用 InMemorySaver 实现内存检查点
- 多线程对话的隔离机制
- 检查点的管理和监控

## 📚 核心概念

### 1. 什么是检查点？

检查点（Checkpoint）是 LangGraph 中的**状态持久化机制**，用于保存和恢复图的执行状态：

```
用户输入 → 图执行 → 状态更新 → 检查点保存 → 可恢复状态
```

**检查点的作用：**
- **状态持久化**：保存对话历史和上下文
- **会话管理**：支持多用户、多线程对话
- **错误恢复**：异常时可恢复到之前状态
- **时间旅行**：回到历史状态进行调试

### 2. InMemorySaver

InMemorySaver 是内存中的检查点保存器：

```python
from langgraph.checkpoint.memory import InMemorySaver

# 创建内存检查点保存器
memory = InMemorySaver()

# 编译图时启用检查点
graph = graph_builder.compile(checkpointer=memory)
```

**特点：**
- **快速访问**：内存中存储，读写速度快
- **临时性**：程序重启后数据丢失
- **适用场景**：开发测试、短期会话

### 3. 线程配置

每个对话线程需要唯一的配置：

```python
config = {"configurable": {"thread_id": "conversation_1"}}

# 使用配置调用图
result = graph.invoke(input_data, config)

# 获取状态
state = graph.get_state(config)
```

## 🔍 代码详细解析

### 基础检查点设置

```python
from langgraph.checkpoint.memory import InMemorySaver

# 创建内存检查点保存器
memory = InMemorySaver()

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 编译图（启用检查点）
graph = graph_builder.compile(checkpointer=memory)
```

**关键点：**
- `InMemorySaver()`：创建内存保存器
- `compile(checkpointer=memory)`：启用检查点功能
- 图的每次执行都会自动保存状态

### 线程隔离机制

```python
def run_memory_chatbot():
    """运行带内存的聊天机器人"""
    # 配置线程ID
    config = {"configurable": {"thread_id": "conversation_1"}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        # 调用图（会自动保存和恢复状态）
        result = graph.invoke(
            {"messages": [{"role": "user", "content": user_input}]},
            config
        )

        # 输出回复
        assistant_message = result["messages"][-1]
        print(f"助手: {assistant_message.content}")
```

### 状态查询和历史

```python
def inspect_conversation_history(config):
    """检查对话历史"""
    try:
        # 获取当前状态
        current_state = graph.get_state(config)

        if current_state.values:
            messages = current_state.values.get("messages", [])
            print(f"\n=== 对话历史 ({len(messages)} 条消息) ===")

            for i, msg in enumerate(messages, 1):
                role = "用户" if msg.get("role") == "user" else "助手"
                content = msg.get("content", "")
                print(f"{i}. {role}: {content[:100]}...")
        else:
            print("没有对话历史")

    except Exception as e:
        print(f"获取历史失败: {e}")
```

## 🚀 运行演示

### 多线程对话演示

```python
def demo_multiple_threads():
    """演示多线程对话"""
    # 创建两个不同的对话线程
    thread1_config = {"configurable": {"thread_id": "user_alice"}}
    thread2_config = {"configurable": {"thread_id": "user_bob"}}

    # 线程1的对话
    print("\n=== Alice 的对话 ===")
    graph.invoke(
        {"messages": [{"role": "user", "content": "我叫 Alice，我喜欢编程"}]},
        thread1_config
    )

    # 线程2的对话
    print("\n=== Bob 的对话 ===")
    graph.invoke(
        {"messages": [{"role": "user", "content": "我叫 Bob，我喜欢音乐"}]},
        thread2_config
    )

    # 继续线程1的对话
    print("\n=== Alice 继续对话 ===")
    result1 = graph.invoke(
        {"messages": [{"role": "user", "content": "你还记得我的名字和爱好吗？"}]},
        thread1_config
    )
    print(f"回复: {result1['messages'][-1].content}")

    # 继续线程2的对话
    print("\n=== Bob 继续对话 ===")
    result2 = graph.invoke(
        {"messages": [{"role": "user", "content": "你还记得我的名字和爱好吗？"}]},
        thread2_config
    )
    print(f"回复: {result2['messages'][-1].content}")
```

### 预期输出

```
=== Alice 的对话 ===
助手: 你好 Alice！很高兴认识你。编程是一个很有趣的爱好！

=== Bob 的对话 ===
助手: 你好 Bob！很高兴认识你。音乐是一个很棒的爱好！

=== Alice 继续对话 ===
回复: 当然记得！你是 Alice，你喜欢编程。

=== Bob 继续对话 ===
回复: 当然记得！你是 Bob，你喜欢音乐。
```

## 🎯 高级检查点管理

### 1. 检查点监控

```python
def inspect_checkpointer():
    """检查检查点保存器的内部状态"""
    print("\n检查点保存器状态检查")
    print("="*50)

    # 创建一些测试状态
    test_configs = [
        {"configurable": {"thread_id": "test_1"}},
        {"configurable": {"thread_id": "test_2"}},
        {"configurable": {"thread_id": "test_3"}},
    ]

    # 为每个测试线程创建一些对话
    for i, config in enumerate(test_configs, 1):
        print(f"\n创建测试线程 {i}...")
        graph.invoke(
            {"messages": [{"role": "user", "content": f"这是测试线程 {i}"}]},
            config
        )

        # 获取状态
        state = graph.get_state(config)
        print(f"线程 {i} 状态:")
        print(f"  消息数量: {len(state.values.get('messages', []))}")
        print(f"  检查点ID: {state.config['configurable']['checkpoint_id']}")
```

### 2. 状态比较和分析

```python
def compare_thread_states():
    """比较不同线程的状态"""
    configs = [
        {"configurable": {"thread_id": "user_alice"}},
        {"configurable": {"thread_id": "user_bob"}}
    ]

    states = []
    for config in configs:
        try:
            state = graph.get_state(config)
            states.append({
                "thread_id": config["configurable"]["thread_id"],
                "message_count": len(state.values.get("messages", [])),
                "checkpoint_id": state.config["configurable"]["checkpoint_id"],
                "state_values": state.values
            })
        except Exception as e:
            print(f"获取状态失败: {e}")

    # 比较状态
    print("\n=== 线程状态比较 ===")
    for state_info in states:
        print(f"线程: {state_info['thread_id']}")
        print(f"  消息数: {state_info['message_count']}")
        print(f"  检查点: {state_info['checkpoint_id'][:8]}...")
        print()
```

### 3. 内存使用监控

```python
import sys
import gc

def monitor_memory_usage():
    """监控内存使用情况"""
    # 强制垃圾回收
    gc.collect()

    # 获取内存使用信息
    memory_info = {
        "objects_count": len(gc.get_objects()),
        "memory_usage_mb": sys.getsizeof(memory) / (1024 * 1024),
    }

    print(f"\n=== 内存使用监控 ===")
    print(f"对象数量: {memory_info['objects_count']}")
    print(f"检查点保存器内存: {memory_info['memory_usage_mb']:.2f} MB")

    # 检查是否有内存泄漏
    if memory_info['objects_count'] > 10000:
        print("⚠️  警告：对象数量过多，可能存在内存泄漏")
```

## 🎯 实践练习

### 练习1：会话管理器

```python
class SessionManager:
    """会话管理器"""

    def __init__(self, graph):
        self.graph = graph
        self.active_sessions = {}
        self.session_metadata = {}

    def create_session(self, user_id: str, session_name: str = None) -> str:
        """创建新会话"""
        import uuid
        session_id = str(uuid.uuid4())[:8]

        config = {"configurable": {"thread_id": session_id}}

        self.active_sessions[session_id] = {
            "user_id": user_id,
            "config": config,
            "created_at": datetime.datetime.now(),
            "last_activity": datetime.datetime.now()
        }

        self.session_metadata[session_id] = {
            "name": session_name or f"会话_{session_id}",
            "message_count": 0,
            "status": "active"
        }

        return session_id

    def get_session(self, session_id: str) -> dict:
        """获取会话信息"""
        if session_id not in self.active_sessions:
            raise ValueError(f"会话 {session_id} 不存在")

        return self.active_sessions[session_id]

    def send_message(self, session_id: str, message: str) -> str:
        """发送消息到会话"""
        session = self.get_session(session_id)
        config = session["config"]

        # 更新最后活动时间
        session["last_activity"] = datetime.datetime.now()

        # 发送消息
        result = self.graph.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config
        )

        # 更新元数据
        self.session_metadata[session_id]["message_count"] += 1

        return result["messages"][-1].content

    def list_sessions(self, user_id: str = None) -> list:
        """列出会话"""
        sessions = []
        for session_id, session_info in self.active_sessions.items():
            if user_id is None or session_info["user_id"] == user_id:
                metadata = self.session_metadata[session_id]
                sessions.append({
                    "session_id": session_id,
                    "user_id": session_info["user_id"],
                    "name": metadata["name"],
                    "message_count": metadata["message_count"],
                    "last_activity": session_info["last_activity"],
                    "status": metadata["status"]
                })

        return sessions

# 使用示例
session_manager = SessionManager(graph)

# 创建会话
session_id = session_manager.create_session("user_123", "编程讨论")

# 发送消息
response = session_manager.send_message(session_id, "你好，我想学习 Python")
print(f"回复: {response}")

# 列出会话
sessions = session_manager.list_sessions("user_123")
for session in sessions:
    print(f"会话: {session['name']}, 消息数: {session['message_count']}")
```

### 练习2：检查点清理

```python
import datetime

def cleanup_old_checkpoints():
    """清理过期的检查点"""
    # 注意：InMemorySaver 不直接支持清理操作
    # 这里演示清理逻辑的概念

    cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=24)

    # 模拟检查点清理
    print("开始清理过期检查点...")

    # 在实际应用中，你可能需要：
    # 1. 遍历所有检查点
    # 2. 检查创建时间
    # 3. 删除过期的检查点

    print("检查点清理完成")

def optimize_memory():
    """优化内存使用"""
    import gc

    # 强制垃圾回收
    collected = gc.collect()
    print(f"垃圾回收释放了 {collected} 个对象")

    # 检查内存使用
    monitor_memory_usage()
```

### 练习3：检查点备份

```python
import json
import pickle

def backup_checkpoints():
    """备份检查点数据"""
    # 注意：这是概念性示例，InMemorySaver 的内部数据不直接可访问

    backup_data = {
        "timestamp": datetime.datetime.now().isoformat(),
        "sessions": [],
        "metadata": {}
    }

    # 在实际应用中，你需要遍历所有活跃会话
    for session_id in ["test_1", "test_2", "test_3"]:
        try:
            config = {"configurable": {"thread_id": session_id}}
            state = graph.get_state(config)

            if state.values:
                backup_data["sessions"].append({
                    "session_id": session_id,
                    "state": state.values,
                    "checkpoint_id": state.config["configurable"]["checkpoint_id"]
                })
        except Exception as e:
            print(f"备份会话 {session_id} 失败: {e}")

    # 保存备份
    backup_file = f"checkpoint_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"检查点备份完成: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"备份失败: {e}")
        return None
```

## 🔧 常见问题

### Q1: 内存检查点会占用多少内存？

**答：** 内存使用量取决于状态大小和会话数量：

```python
def estimate_memory_usage():
    """估算内存使用量"""
    # 单个消息大约 1KB
    # 50条消息的对话约 50KB
    # 100个并发会话约 5MB

    sessions = 100
    messages_per_session = 50
    bytes_per_message = 1024

    total_memory = sessions * messages_per_session * bytes_per_message
    print(f"估算内存使用: {total_memory / (1024*1024):.2f} MB")
```

### Q2: 如何处理内存不足的情况？

**答：** 实现内存限制和清理策略：

```python
def check_memory_limit():
    """检查内存限制"""
    import psutil

    # 获取当前内存使用
    memory = psutil.virtual_memory()

    if memory.percent > 80:  # 内存使用超过80%
        print("⚠️  内存使用过高，开始清理...")
        cleanup_old_checkpoints()
        optimize_memory()
```

### Q3: InMemorySaver 适合生产环境吗？

**答：** 不适合。生产环境建议使用持久化存储：

```python
# 生产环境推荐使用 SQLite 或其他持久化存储
from langgraph.checkpoint.sqlite import SqliteSaver

# SQLite 检查点保存器
checkpointer = SqliteSaver.from_conn_string("sqlite:///checkpoints.db")
graph = graph_builder.compile(checkpointer=checkpointer)
```

## 📖 相关资源

### 官方文档
- [LangGraph 检查点](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [内存保存器](https://langchain-ai.github.io/langgraph/reference/checkpoints/#memorysaver)

### 下一步学习
- [07. SQLite 检查点教学](07_sqlite_checkpoint_tutorial.md) - 持久化存储
- [09. 时间旅行教学](09_time_travel_tutorial.md) - 状态回溯

### 代码示例
- 完整代码：[06_memory_checkpoint.py](../../teach_code/06_memory_checkpoint.py)
- 运行方式：`python teach_code/06_memory_checkpoint.py`

## 🌟 总结

内存检查点是 LangGraph 状态管理的基础：

1. **快速访问**：内存中存储，性能优异
2. **线程隔离**：支持多用户并发对话
3. **自动管理**：透明的状态保存和恢复
4. **开发友好**：适合开发测试环境
5. **临时性**：程序重启后数据丢失

掌握内存检查点后，你可以构建有状态的对话应用！
