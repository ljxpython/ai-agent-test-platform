# 07. SQLite 检查点教学

## 🎯 学习目标

通过这个教程，你将学会：
- SQLite 检查点的优势和应用场景
- 如何配置和使用 SqliteSaver
- 数据库持久化的最佳实践
- 检查点数据的查询和管理

## 📚 核心概念

### 1. 什么是 SQLite 检查点？

SQLite 检查点是将图状态**持久化到数据库**的机制，相比内存检查点具有以下优势：

```
内存检查点 → 程序重启后丢失
SQLite 检查点 → 永久保存，可跨会话恢复
```

**SQLite 检查点的特点：**
- **持久化存储**：数据保存在磁盘上
- **跨会话恢复**：程序重启后可恢复状态
- **并发支持**：多进程可共享同一数据库
- **查询能力**：可直接查询检查点数据

### 2. SqliteSaver 配置

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import tempfile
import os

# 创建数据库路径
db_path = os.path.join(tempfile.gettempdir(), "langgraph_checkpoint.db")

# 创建 SQLite 检查点保存器
checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")

# 编译图（启用 SQLite 检查点）
graph = graph_builder.compile(checkpointer=checkpointer)
```

### 3. 数据库结构

SQLite 检查点会创建以下表结构：
- **checkpoints**：存储检查点数据
- **writes**：存储状态写入记录
- **metadata**：存储元数据信息

## 🔍 代码详细解析

### 基础 SQLite 设置

```python
import tempfile
import os
from langgraph.checkpoint.sqlite import SqliteSaver

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
```

**关键点：**
- `SqliteSaver.from_conn_string()`：从连接字符串创建保存器
- 数据库文件会自动创建
- 支持相对路径和绝对路径

### 持久化演示

```python
def demo_persistence():
    """演示持久化功能"""
    # 创建一个测试线程
    test_thread = "persistence_test"
    config = {"configurable": {"thread_id": test_thread}}

    print(f"创建测试对话线程: {test_thread}")

    # 第一轮对话
    print("\n=== 第一轮对话 ===")
    result1 = graph.invoke(
        {"messages": [{"role": "user", "content": "我叫张三，我是一名程序员"}]},
        config
    )
    print(f"助手: {result1['messages'][-1].content}")

    # 第二轮对话
    print("\n=== 第二轮对话 ===")
    result2 = graph.invoke(
        {"messages": [{"role": "user", "content": "我喜欢用 Python 编程"}]},
        config
    )
    print(f"助手: {result2['messages'][-1].content}")

    # 模拟程序重启 - 重新创建图和检查点保存器
    print("\n=== 模拟程序重启 ===")
    new_checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")
    new_graph = graph_builder.compile(checkpointer=new_checkpointer)

    # 恢复对话
    print("\n=== 恢复对话 ===")
    result3 = new_graph.invoke(
        {"messages": [{"role": "user", "content": "你还记得我的名字和职业吗？"}]},
        config
    )
    print(f"助手: {result3['messages'][-1].content}")
```

### 数据库检查

```python
def inspect_database():
    """检查数据库内容"""
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
        if ('checkpoints',) in tables:
            cursor.execute("SELECT COUNT(*) FROM checkpoints;")
            count = cursor.fetchone()[0]
            print(f"检查点记录数: {count}")

            # 查看最近的几个检查点
            cursor.execute("""
                SELECT thread_id, checkpoint_id, created_at
                FROM checkpoints
                ORDER BY created_at DESC
                LIMIT 5
            """)
            recent_checkpoints = cursor.fetchall()
            print("\n最近的检查点:")
            for thread_id, checkpoint_id, created_at in recent_checkpoints:
                print(f"  线程: {thread_id}, 检查点: {checkpoint_id[:8]}..., 时间: {created_at}")

        conn.close()

    except Exception as e:
        print(f"检查数据库失败: {e}")
```

## 🚀 运行演示

### 基础 SQLite 演示

```python
def run_sqlite_chatbot():
    """运行带 SQLite 持久化的聊天机器人"""
    print("带 SQLite 持久化的聊天机器人启动！")
    print("对话历史会保存到数据库中，重启后仍然可用。")

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
            break

        try:
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config
            )

            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")
```

### 预期输出

```
使用数据库: /tmp/langgraph_checkpoint.db
带 SQLite 持久化的聊天机器人启动！

请输入线程ID（直接回车创建新线程）: test_user
=== 恢复线程 test_user 的历史 ===
用户: 我叫张三
助手: 你好张三！很高兴认识你。

[test_user] 用户: 你还记得我的名字吗？
助手: 当然记得！你的名字是张三。
```

## 🎯 高级 SQLite 管理

### 1. 数据库优化

```python
def optimize_database():
    """优化数据库性能"""
    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 分析表统计信息
        cursor.execute("ANALYZE;")

        # 清理碎片
        cursor.execute("VACUUM;")

        # 设置性能参数
        cursor.execute("PRAGMA journal_mode=WAL;")  # 写前日志模式
        cursor.execute("PRAGMA synchronous=NORMAL;")  # 同步模式
        cursor.execute("PRAGMA cache_size=10000;")  # 缓存大小

        conn.commit()
        conn.close()

        print("数据库优化完成")

    except Exception as e:
        print(f"数据库优化失败: {e}")

def get_database_stats():
    """获取数据库统计信息"""
    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 数据库大小
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();")
        size = cursor.fetchone()[0]

        # 表统计
        stats = {"database_size_mb": size / (1024 * 1024)}

        tables = ["checkpoints", "writes"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                stats[f"{table}_count"] = count
            except:
                stats[f"{table}_count"] = 0

        conn.close()

        print("数据库统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

        return stats

    except Exception as e:
        print(f"获取统计信息失败: {e}")
        return {}
```

### 2. 数据清理

```python
import datetime

def cleanup_old_checkpoints(days_old: int = 7):
    """清理旧的检查点"""
    try:
        import sqlite3

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 计算截止时间
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)
        cutoff_timestamp = cutoff_date.isoformat()

        # 查询要删除的记录数
        cursor.execute("""
            SELECT COUNT(*) FROM checkpoints
            WHERE created_at < ?
        """, (cutoff_timestamp,))

        count_to_delete = cursor.fetchone()[0]

        if count_to_delete > 0:
            print(f"准备删除 {count_to_delete} 个旧检查点...")

            # 删除旧检查点
            cursor.execute("""
                DELETE FROM checkpoints
                WHERE created_at < ?
            """, (cutoff_timestamp,))

            # 删除相关的写入记录
            cursor.execute("""
                DELETE FROM writes
                WHERE created_at < ?
            """, (cutoff_timestamp,))

            conn.commit()
            print(f"已删除 {count_to_delete} 个旧检查点")
        else:
            print("没有需要清理的旧检查点")

        conn.close()

    except Exception as e:
        print(f"清理检查点失败: {e}")

def backup_database(backup_path: str):
    """备份数据库"""
    try:
        import sqlite3
        import shutil

        # 简单的文件复制备份
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")

        # 或者使用 SQLite 的备份 API
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(backup_path + ".backup")

        source.backup(backup)

        source.close()
        backup.close()

        print(f"数据库已备份到: {backup_path}.backup")

    except Exception as e:
        print(f"备份失败: {e}")
```

### 3. 检查点查询

```python
def query_checkpoints(thread_id: str = None, limit: int = 10):
    """查询检查点数据"""
    try:
        import sqlite3
        import json

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if thread_id:
            cursor.execute("""
                SELECT thread_id, checkpoint_id, created_at, checkpoint
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (thread_id, limit))
        else:
            cursor.execute("""
                SELECT thread_id, checkpoint_id, created_at, checkpoint
                FROM checkpoints
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        checkpoints = cursor.fetchall()

        print(f"查询到 {len(checkpoints)} 个检查点:")
        for thread_id, checkpoint_id, created_at, checkpoint_data in checkpoints:
            print(f"\n线程: {thread_id}")
            print(f"检查点ID: {checkpoint_id[:8]}...")
            print(f"创建时间: {created_at}")

            # 尝试解析检查点数据
            try:
                if checkpoint_data:
                    # 检查点数据通常是序列化的
                    print(f"数据大小: {len(str(checkpoint_data))} 字符")
            except:
                print("无法解析检查点数据")

        conn.close()

    except Exception as e:
        print(f"查询检查点失败: {e}")

def export_conversation_history(thread_id: str, output_file: str):
    """导出对话历史"""
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = graph.get_state(config)

        if state.values and "messages" in state.values:
            messages = state.values["messages"]

            # 格式化对话历史
            conversation = {
                "thread_id": thread_id,
                "export_time": datetime.datetime.now().isoformat(),
                "message_count": len(messages),
                "messages": []
            }

            for msg in messages:
                conversation["messages"].append({
                    "role": msg.get("role", "unknown"),
                    "content": msg.get("content", ""),
                    "timestamp": getattr(msg, "timestamp", None)
                })

            # 保存到文件
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)

            print(f"对话历史已导出到: {output_file}")
            print(f"包含 {len(messages)} 条消息")

        else:
            print(f"线程 {thread_id} 没有对话历史")

    except Exception as e:
        print(f"导出失败: {e}")
```

## 🎯 实践练习

### 练习1：多数据库管理

```python
class DatabaseManager:
    """数据库管理器"""

    def __init__(self, base_path: str = "checkpoints"):
        self.base_path = base_path
        self.databases = {}
        os.makedirs(base_path, exist_ok=True)

    def get_database(self, db_name: str):
        """获取或创建数据库"""
        if db_name not in self.databases:
            db_path = os.path.join(self.base_path, f"{db_name}.db")
            checkpointer = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")

            self.databases[db_name] = {
                "path": db_path,
                "checkpointer": checkpointer,
                "graph": graph_builder.compile(checkpointer=checkpointer)
            }

        return self.databases[db_name]

    def list_databases(self):
        """列出所有数据库"""
        db_files = [f for f in os.listdir(self.base_path) if f.endswith('.db')]

        print("可用的数据库:")
        for db_file in db_files:
            db_name = db_file[:-3]  # 移除 .db 后缀
            db_path = os.path.join(self.base_path, db_file)
            size = os.path.getsize(db_path) / 1024  # KB
            print(f"  {db_name}: {size:.1f} KB")

    def migrate_data(self, source_db: str, target_db: str):
        """数据迁移"""
        try:
            source_info = self.get_database(source_db)
            target_info = self.get_database(target_db)

            # 这里可以实现具体的数据迁移逻辑
            print(f"数据迁移: {source_db} -> {target_db}")

        except Exception as e:
            print(f"数据迁移失败: {e}")

# 使用示例
db_manager = DatabaseManager()

# 创建不同用途的数据库
dev_db = db_manager.get_database("development")
prod_db = db_manager.get_database("production")
test_db = db_manager.get_database("testing")

# 列出数据库
db_manager.list_databases()
```

### 练习2：性能监控

```python
import time
import threading

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.metrics = {
            "total_operations": 0,
            "total_time": 0,
            "avg_response_time": 0,
            "operations_per_second": 0
        }
        self.lock = threading.Lock()

    def record_operation(self, operation_time: float):
        """记录操作时间"""
        with self.lock:
            self.metrics["total_operations"] += 1
            self.metrics["total_time"] += operation_time

            if self.metrics["total_operations"] > 0:
                self.metrics["avg_response_time"] = (
                    self.metrics["total_time"] / self.metrics["total_operations"]
                )

    def get_metrics(self):
        """获取性能指标"""
        with self.lock:
            # 计算每秒操作数（简化计算）
            if self.metrics["total_time"] > 0:
                self.metrics["operations_per_second"] = (
                    self.metrics["total_operations"] / self.metrics["total_time"]
                )

            return self.metrics.copy()

    def monitor_database_size(self):
        """监控数据库大小"""
        try:
            size = os.path.getsize(self.db_path) / (1024 * 1024)  # MB
            return size
        except:
            return 0

def monitored_graph_invoke(graph, input_data, config, monitor):
    """带监控的图调用"""
    start_time = time.time()

    try:
        result = graph.invoke(input_data, config)
        return result
    finally:
        operation_time = time.time() - start_time
        monitor.record_operation(operation_time)

# 使用示例
monitor = PerformanceMonitor(db_path)

# 监控图调用
config = {"configurable": {"thread_id": "perf_test"}}
result = monitored_graph_invoke(
    graph,
    {"messages": [{"role": "user", "content": "测试性能"}]},
    config,
    monitor
)

# 查看性能指标
metrics = monitor.get_metrics()
print(f"性能指标: {metrics}")
```

### 练习3：数据恢复

```python
def create_recovery_point(name: str):
    """创建恢复点"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        recovery_file = f"recovery_{name}_{timestamp}.db"

        backup_database(recovery_file)

        # 记录恢复点信息
        recovery_info = {
            "name": name,
            "timestamp": timestamp,
            "file": recovery_file,
            "database_stats": get_database_stats()
        }

        info_file = f"recovery_{name}_{timestamp}.json"
        with open(info_file, 'w') as f:
            json.dump(recovery_info, f, indent=2, default=str)

        print(f"恢复点已创建: {name}")
        return recovery_file

    except Exception as e:
        print(f"创建恢复点失败: {e}")
        return None

def restore_from_recovery_point(recovery_file: str):
    """从恢复点恢复"""
    try:
        if not os.path.exists(recovery_file):
            print(f"恢复文件不存在: {recovery_file}")
            return False

        # 备份当前数据库
        current_backup = f"current_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_database(current_backup)
        print(f"当前数据库已备份到: {current_backup}")

        # 恢复数据库
        shutil.copy2(recovery_file, db_path)
        print(f"数据库已从恢复点恢复: {recovery_file}")

        return True

    except Exception as e:
        print(f"恢复失败: {e}")
        return False
```

## 🔧 常见问题

### Q1: SQLite 数据库文件过大怎么办？

**答：** 实现定期清理和压缩：

```python
def compress_database():
    """压缩数据库"""
    try:
        import sqlite3

        conn = sqlite3.connect(db_path)

        # 清理碎片
        conn.execute("VACUUM;")

        # 重建索引
        conn.execute("REINDEX;")

        conn.close()
        print("数据库压缩完成")

    except Exception as e:
        print(f"压缩失败: {e}")
```

### Q2: 如何处理数据库锁定问题？

**答：** 使用连接池和重试机制：

```python
import time
import random

def robust_database_operation(operation_func, max_retries=3):
    """健壮的数据库操作"""
    for attempt in range(max_retries):
        try:
            return operation_func()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                # 随机等待后重试
                wait_time = random.uniform(0.1, 0.5)
                time.sleep(wait_time)
                continue
            else:
                raise
```

### Q3: SQLite 适合高并发场景吗？

**答：** SQLite 适合中等并发，高并发建议使用 PostgreSQL：

```python
# 高并发场景的替代方案
from langgraph.checkpoint.postgres import PostgresSaver

# PostgreSQL 检查点保存器
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/langgraph"
)
```

## 📖 相关资源

### 官方文档
- [LangGraph SQLite 检查点](https://langchain-ai.github.io/langgraph/reference/checkpoints/#sqlitesaver)
- [SQLite 最佳实践](https://www.sqlite.org/bestpractices.html)

### 下一步学习
- [06. 内存检查点教学](06_memory_checkpoint_tutorial.md) - 内存检查点对比
- [09. 时间旅行教学](09_time_travel_tutorial.md) - 状态回溯

### 代码示例
- 完整代码：[07_sqlite_checkpoint.py](../../teach_code/07_sqlite_checkpoint.py)
- 运行方式：`python teach_code/07_sqlite_checkpoint.py`

## 🌟 总结

SQLite 检查点是生产环境的理想选择：

1. **持久化存储**：数据永久保存，不会丢失
2. **跨会话恢复**：程序重启后可恢复状态
3. **查询能力**：可直接查询和分析数据
4. **性能优化**：支持索引、压缩、清理
5. **备份恢复**：完整的数据管理能力

掌握 SQLite 检查点后，你可以构建企业级的持久化应用！
