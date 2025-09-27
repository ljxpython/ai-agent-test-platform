# 01. 基础聊天机器人教学

## 🎯 学习目标

通过这个教程，你将学会：
- LangGraph 的核心概念：图、节点、边、状态
- 如何创建最简单的聊天机器人
- 状态管理的基本原理
- 消息流的处理方式

## 📚 核心概念

### 1. 什么是 LangGraph？

LangGraph 是一个用于构建**有状态、多轮对话应用**的框架。与传统的链式方法不同，LangGraph 将应用建模为**有向图**：

```
节点（Nodes） → 执行单元（函数）
边（Edges） → 控制流（路由逻辑）
状态（State） → 数据流（共享状态）
```

### 2. 状态（State）

状态是图中所有节点共享的数据结构。在我们的聊天机器人中：

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

**关键点：**
- `TypedDict`：提供类型安全
- `Annotated[list, add_messages]`：定义消息列表的合并策略
- `add_messages`：自动处理消息的追加和去重

### 3. 节点（Nodes）

节点是图中的执行单元，本质上是函数：

```python
def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}
```

**函数签名规则：**
- 输入：当前状态
- 输出：状态更新字典
- 只需返回要更新的字段

### 4. 图构建

```python
# 1. 创建图构建器
graph_builder = StateGraph(State)

# 2. 添加节点
graph_builder.add_node("chatbot", chatbot)

# 3. 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# 4. 编译图
graph = graph_builder.compile()
```

## 🔍 代码详细解析

### 导入和配置

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from config import llm
```

**解释：**
- `Annotated`：用于类型注解和元数据
- `TypedDict`：类型安全的字典定义
- `StateGraph`：LangGraph 的核心图类
- `START, END`：特殊的图节点标识符
- `add_messages`：消息合并函数

### 状态定义

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
```

**深入理解：**
- `messages` 字段存储对话历史
- `add_messages` 确保消息正确追加
- 支持消息去重和格式标准化

### 聊天机器人节点

```python
def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm.invoke(state["messages"])]}
```

**执行流程：**
1. 接收当前状态（包含消息历史）
2. 调用 LLM 生成回复
3. 返回包含新消息的更新字典

### 图的构建和编译

```python
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()
```

**图结构：**
```
START → chatbot → END
```

## 🚀 运行演示

### 基本使用

```python
result = graph.invoke({
    "messages": [{"role": "user", "content": "你好"}]
})

# 输出回复
assistant_message = result["messages"][-1]
print(f"助手: {assistant_message.content}")
```

### 交互式对话

```python
def run_chatbot():
    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        result = graph.invoke({
            "messages": [{"role": "user", "content": user_input}]
        })

        assistant_message = result["messages"][-1]
        print(f"助手: {assistant_message.content}")
```

### 预期输出

```
用户: 你好
助手: 你好！我是你的AI助手，有什么可以帮助你的吗？

用户: 今天天气怎么样？
助手: 我无法获取实时天气信息，建议你查看天气应用或网站获取准确的天气预报。

用户: quit
再见！
```

## 🔧 常见问题

### Q1: 为什么使用 TypedDict？

**答：** TypedDict 提供类型安全，帮助：
- IDE 自动补全
- 类型检查
- 代码可读性
- 运行时验证

### Q2: add_messages 函数的作用？

**答：** add_messages 处理消息合并：
- 自动追加新消息
- 去除重复消息
- 保持消息格式一致
- 支持不同消息类型

### Q3: 如何处理长对话历史？

**答：** 可以在节点中截断历史：

```python
def chatbot(state: State):
    messages = state["messages"]
    # 只保留最近10条消息
    recent_messages = messages[-10:]
    response = llm.invoke(recent_messages)
    return {"messages": [response]}
```

### Q4: 如何添加系统提示？

**答：** 在调用 LLM 前添加系统消息：

```python
def chatbot(state: State):
    messages = state["messages"]
    system_message = {"role": "system", "content": "你是一个友好的助手"}
    full_messages = [system_message] + messages
    response = llm.invoke(full_messages)
    return {"messages": [response]}
```

## 🎯 实践练习

### 练习1：添加用户名记忆

修改状态以记住用户名：

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str

def chatbot(state: State):
    messages = state["messages"]
    user_name = state.get("user_name", "朋友")

    # 在系统提示中使用用户名
    system_prompt = f"你是一个友好的助手，用户名是{user_name}"
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages

    response = llm.invoke(enhanced_messages)
    return {"messages": [response]}
```

### 练习2：添加消息计数

跟踪对话轮数：

```python
class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_count: Annotated[int, lambda x, y: x + y]

def chatbot(state: State):
    messages = state["messages"]
    count = state.get("message_count", 0)

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "message_count": 1  # 增加计数
    }
```

### 练习3：添加情感分析

分析用户情感并相应回复：

```python
def analyze_sentiment(content: str) -> str:
    positive_words = ["好", "棒", "喜欢", "开心"]
    negative_words = ["坏", "差", "讨厌", "生气"]

    if any(word in content for word in positive_words):
        return "positive"
    elif any(word in content for word in negative_words):
        return "negative"
    return "neutral"

def chatbot(state: State):
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if last_message and last_message.get("role") == "user":
        sentiment = analyze_sentiment(last_message.get("content", ""))

        if sentiment == "positive":
            system_prompt = "用户情绪积极，请保持友好热情的回复"
        elif sentiment == "negative":
            system_prompt = "用户情绪消极，请给予安慰和支持"
        else:
            system_prompt = "正常友好地回复用户"

        enhanced_messages = [{"role": "system", "content": system_prompt}] + messages
    else:
        enhanced_messages = messages

    response = llm.invoke(enhanced_messages)
    return {"messages": [response]}
```

## 📖 相关资源

### 官方文档
- [LangGraph 快速开始](https://langchain-ai.github.io/langgraph/tutorials/introduction/)
- [状态管理指南](https://langchain-ai.github.io/langgraph/concepts/low_level/#state)
- [消息处理](https://langchain-ai.github.io/langgraph/concepts/low_level/#messages)

### 下一步学习
- [02. 流式处理教学](02_streaming_tutorial.md) - 学习实时响应
- [03. 工具集成教学](03_tools_integration_tutorial.md) - 添加外部工具
- [05. 状态管理教学](05_state_management_tutorial.md) - 复杂状态设计

### 代码示例
- 完整代码：[01_basic_chatbot.py](../../teach_code/01_basic_chatbot.py)
- 运行方式：`python teach_code/01_basic_chatbot.py`

## 🌟 总结

这个基础聊天机器人教程介绍了 LangGraph 的核心概念：

1. **图结构**：节点执行逻辑，边控制流程
2. **状态管理**：TypedDict 定义，自动合并策略
3. **消息处理**：add_messages 函数的重要性
4. **简单交互**：用户输入到 AI 回复的完整流程

掌握这些基础概念后，你就可以构建更复杂的 LangGraph 应用了！
