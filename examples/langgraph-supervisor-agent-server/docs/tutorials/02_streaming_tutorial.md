# 02. 流式处理教学

## 🎯 学习目标

通过这个教程，你将学会：
- 什么是流式处理及其优势
- 如何实现 LangGraph 的流式输出
- 流式处理的应用场景
- 实时响应的最佳实践

## 📚 核心概念

### 1. 什么是流式处理？

流式处理是指**实时处理和输出数据**，而不是等待整个处理完成后再返回结果。在聊天应用中，这意味着：

```
传统方式：用户输入 → 等待 → 完整回复
流式方式：用户输入 → 逐字输出 → 实时显示
```

**优势：**
- 更好的用户体验（即时反馈）
- 降低感知延迟
- 适合长文本生成
- 可以提前中断处理

### 2. LangGraph 中的流式处理

LangGraph 提供了 `stream()` 方法来实现流式处理：

```python
# 传统方式
result = graph.invoke(input_data)

# 流式方式
for event in graph.stream(input_data):
    # 处理每个事件
    process_event(event)
```

### 3. 流式事件结构

每个流式事件包含：
- **节点名称**：当前执行的节点
- **状态更新**：节点产生的状态变化
- **消息内容**：新生成的消息

## 🔍 代码详细解析

### 基础流式实现

```python
def stream_graph_updates(user_input: str):
    """流式处理图更新"""
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            if "messages" in value:
                print("助手:", value["messages"][-1].content)
```

**执行流程：**
1. `graph.stream()` 启动流式处理
2. 每个节点执行完成后产生一个事件
3. 事件包含该节点的状态更新
4. 实时输出新生成的消息

### 事件处理详解

```python
for event in graph.stream(input_data):
    # event 是一个字典，键为节点名，值为状态更新
    for node_name, state_update in event.items():
        print(f"节点 {node_name} 更新: {state_update}")

        # 检查是否有新消息
        if "messages" in state_update:
            new_messages = state_update["messages"]
            for message in new_messages:
                if hasattr(message, 'content'):
                    print(f"新消息: {message.content}")
```

### 错误处理

```python
def safe_stream_processing(user_input: str):
    """安全的流式处理"""
    try:
        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
            for value in event.values():
                if "messages" in value:
                    message = value["messages"][-1]
                    if hasattr(message, 'content') and message.content:
                        print(f"助手: {message.content}")
    except Exception as e:
        print(f"流式处理错误: {e}")
```

## 🚀 运行演示

### 基础流式聊天

```python
def run_streaming_chatbot():
    print("流式聊天机器人启动！")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        # 流式处理用户输入
        print("助手: ", end="", flush=True)
        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
            for value in event.values():
                if "messages" in value:
                    content = value["messages"][-1].content
                    print(content, end="", flush=True)
        print()  # 换行
```

### 预期输出

```
用户: 请介绍一下 Python
助手: Python 是一种高级编程语言，具有简洁的语法和强大的功能...
      [文字逐渐出现，而不是一次性显示]

用户: 它有什么特点？
助手: Python 的主要特点包括：
      1. 语法简洁易读
      2. 跨平台兼容
      3. 丰富的库生态
      [实时显示，用户可以立即看到回复开始]
```

## 🔧 高级流式处理

### 1. 带进度指示的流式处理

```python
def stream_with_progress(user_input: str):
    """带进度指示的流式处理"""
    print("🤔 思考中...", end="", flush=True)

    message_started = False
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for node_name, value in event.items():
            if not message_started:
                print("\r助手: ", end="", flush=True)
                message_started = True

            if "messages" in value:
                content = value["messages"][-1].content
                print(content, end="", flush=True)

    print()  # 换行
```

### 2. 多节点流式监控

```python
def stream_with_node_info(user_input: str):
    """显示节点执行信息的流式处理"""
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for node_name, value in event.items():
            print(f"[{node_name}] ", end="", flush=True)

            if "messages" in value:
                content = value["messages"][-1].content
                print(content)
            else:
                print("处理中...")
```

### 3. 流式处理的性能优化

```python
import asyncio

async def async_stream_processing(user_input: str):
    """异步流式处理"""
    async for event in graph.astream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            if "messages" in value:
                content = value["messages"][-1].content
                print(content, end="", flush=True)

                # 模拟实时处理
                await asyncio.sleep(0.01)
```

## 🎯 实践练习

### 练习1：字符级流式输出

实现字符级的流式输出效果：

```python
import time

def character_stream_output(text: str, delay: float = 0.05):
    """字符级流式输出"""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()

def enhanced_streaming_chatbot():
    """增强的流式聊天机器人"""
    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        print("助手: ", end="", flush=True)

        # 收集完整回复
        full_response = ""
        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
            for value in event.values():
                if "messages" in value:
                    full_response = value["messages"][-1].content

        # 字符级输出
        character_stream_output(full_response)
```

### 练习2：流式处理状态监控

监控流式处理的各种状态：

```python
def stream_with_monitoring(user_input: str):
    """带监控的流式处理"""
    start_time = time.time()
    event_count = 0
    total_chars = 0

    print(f"开始处理: {user_input}")
    print("助手: ", end="", flush=True)

    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        event_count += 1

        for node_name, value in event.items():
            if "messages" in value:
                content = value["messages"][-1].content
                total_chars += len(content)
                print(content, end="", flush=True)

    end_time = time.time()
    duration = end_time - start_time

    print(f"\n\n📊 处理统计:")
    print(f"   耗时: {duration:.2f}秒")
    print(f"   事件数: {event_count}")
    print(f"   字符数: {total_chars}")
    print(f"   速度: {total_chars/duration:.1f} 字符/秒")
```

### 练习3：流式处理的中断机制

实现可中断的流式处理：

```python
import threading
import queue

class InterruptibleStream:
    def __init__(self):
        self.should_stop = False
        self.input_queue = queue.Queue()

    def start_input_monitor(self):
        """启动输入监控线程"""
        def monitor():
            while True:
                user_input = input()
                if user_input.lower() == 'stop':
                    self.should_stop = True
                    break

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()

    def interruptible_stream(self, user_input: str):
        """可中断的流式处理"""
        self.should_stop = False
        self.start_input_monitor()

        print("助手: ", end="", flush=True)
        print("(输入 'stop' 可中断)")

        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
            if self.should_stop:
                print("\n[已中断]")
                break

            for value in event.values():
                if "messages" in value:
                    content = value["messages"][-1].content
                    print(content, end="", flush=True)

        if not self.should_stop:
            print()
```

## 🔧 常见问题

### Q1: 流式处理比普通处理慢吗？

**答：** 不会。流式处理的总时间相同，但用户感知的延迟更低：
- 普通处理：等待时间 = 总处理时间
- 流式处理：等待时间 ≈ 第一个输出的时间

### Q2: 如何处理流式处理中的错误？

**答：** 使用 try-catch 包装流式循环：

```python
def robust_streaming(user_input: str):
    try:
        for event in graph.stream(input_data):
            # 处理事件
            process_event(event)
    except Exception as e:
        print(f"流式处理中断: {e}")
        # 可以选择重试或降级到普通处理
```

### Q3: 流式处理适用于所有场景吗？

**答：** 不是。适用场景：
- ✅ 长文本生成
- ✅ 实时聊天
- ✅ 用户交互应用
- ❌ 批量处理
- ❌ 后台任务
- ❌ API 调用（除非支持流式）

### Q4: 如何在 Web 应用中实现流式处理？

**答：** 使用 Server-Sent Events (SSE) 或 WebSocket：

```python
# FastAPI 示例
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

app = FastAPI()

@app.post("/chat/stream")
async def stream_chat(message: str):
    def generate():
        for event in graph.stream({"messages": [{"role": "user", "content": message}]}):
            for value in event.values():
                if "messages" in value:
                    content = value["messages"][-1].content
                    yield f"data: {content}\n\n"

    return StreamingResponse(generate(), media_type="text/plain")
```

## 📖 相关资源

### 官方文档
- [LangGraph 流式处理](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [异步流式处理](https://langchain-ai.github.io/langgraph/concepts/async/)

### 下一步学习
- [03. 工具集成教学](03_tools_integration_tutorial.md) - 学习工具集成
- [05. 状态管理教学](05_state_management_tutorial.md) - 复杂状态处理

### 代码示例
- 完整代码：[02_streaming_chatbot.py](../../teach_code/02_streaming_chatbot.py)
- 运行方式：`python teach_code/02_streaming_chatbot.py`

## 🌟 总结

流式处理是现代聊天应用的重要特性：

1. **用户体验**：实时反馈，降低感知延迟
2. **技术实现**：使用 `graph.stream()` 方法
3. **事件处理**：监控节点执行和状态更新
4. **错误处理**：robust 的异常处理机制
5. **性能优化**：异步处理和进度监控

掌握流式处理后，你的 LangGraph 应用将具备更好的交互体验！
