# LangGraph 完整教程 - 从入门到精通

## 目录

1. [LangGraph 简介](#1-langgraph-简介)
2. [核心概念](#2-核心概念)
3. [基础入门](#3-基础入门)
4. [状态管理](#4-状态管理)
5. [节点和边](#5-节点和边)
6. [工作流构建](#6-工作流构建)
7. [多智能体系统](#7-多智能体系统)
8. [高级特性](#8-高级特性)
9. [实战案例](#9-实战案例)
10. [最佳实践](#10-最佳实践)

---

## 1. LangGraph 简介

### 1.1 什么是 LangGraph？

LangGraph 是一个用于构建**有状态、多轮对话应用**的低级编排框架。它专门设计用于：

- **构建智能体（Agents）**：具有推理和决策能力的 AI 系统
- **多智能体系统**：多个智能体协作完成复杂任务
- **有状态工作流**：维护对话历史和执行状态
- **人机交互**：支持人工干预和审核
- **生产部署**：提供持久化、监控和错误恢复

### 1.2 为什么选择 LangGraph？

**与传统链式方法的区别：**

```python
# 传统 LangChain 链式方法
chain = prompt | llm | output_parser
result = chain.invoke(input)

# LangGraph 图式方法
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(State)
workflow.add_node("analyze", analyze_node)
workflow.add_node("decide", decide_node)
workflow.add_edge(START, "analyze")
workflow.add_conditional_edges("analyze", should_continue, {"yes": "decide", "no": END})
app = workflow.compile()
```

**核心优势：**
- **循环和条件逻辑**：支持复杂的控制流
- **状态持久化**：自动保存和恢复执行状态
- **人工干预**：可在任意节点暂停等待人工输入
- **错误恢复**：支持重试和错误处理机制
- **可视化调试**：提供图形化的执行流程

### 1.3 应用场景

- **对话式 AI 助手**：多轮对话、上下文理解
- **自动化工作流**：文档处理、数据分析
- **多智能体协作**：研究团队、客服系统
- **决策支持系统**：风险评估、投资建议
- **内容生成管道**：写作助手、代码生成

---

## 2. 核心概念

### 2.1 图（Graph）

LangGraph 将应用建模为**有向图**，其中：

```python
# 图的基本结构
节点（Nodes） → 执行单元（函数）
边（Edges） → 控制流（路由逻辑）
状态（State） → 数据流（共享状态）
```

**图的类型：**
- **StateGraph**：基于状态的图（最常用）
- **MessageGraph**：基于消息的图（已弃用，推荐使用 StateGraph）

### 2.2 状态（State）

状态是图中所有节点共享的数据结构：

```python
from typing_extensions import TypedDict
from typing import Annotated
import operator

class State(TypedDict):
    messages: Annotated[list, operator.add]  # 消息列表，支持追加
    user_input: str                          # 用户输入
    result: str                              # 处理结果
    step_count: int                          # 步骤计数
```

**状态特性：**
- **类型安全**：使用 TypedDict 定义结构
- **自动合并**：支持自定义合并策略
- **部分更新**：节点只需返回要更新的字段
- **历史追踪**：自动保存状态变更历史

### 2.3 节点（Nodes）

节点是图中的执行单元，本质上是函数：

```python
def my_node(state: State) -> dict:
    """
    节点函数的标准签名：
    - 输入：当前状态
    - 输出：状态更新字典
    """
    # 处理逻辑
    new_result = process_data(state["user_input"])

    # 返回状态更新
    return {
        "result": new_result,
        "step_count": state["step_count"] + 1
    }
```

**节点类型：**
- **普通节点**：执行业务逻辑
- **条件节点**：根据状态决定下一步
- **工具节点**：调用外部工具或 API
- **人工节点**：等待人工干预

### 2.4 边（Edges）

边定义节点之间的连接和路由逻辑：

```python
# 1. 简单边：固定路由
workflow.add_edge("node_a", "node_b")

# 2. 条件边：动态路由
def route_condition(state: State) -> str:
    if state["result"] == "success":
        return "success_node"
    else:
        return "error_node"

workflow.add_conditional_edges(
    "decision_node",
    route_condition,
    {
        "success_node": "process_success",
        "error_node": "handle_error"
    }
)

# 3. 特殊节点
from langgraph.graph import START, END
workflow.add_edge(START, "first_node")  # 入口点
workflow.add_edge("last_node", END)     # 结束点
```

---

## 3. 基础入门

### 3.1 安装和设置

```bash
# 安装核心包
pip install langgraph

# 安装相关依赖
pip install langchain langchain-openai

# 可选：安装可视化工具
pip install "langgraph[dev]"
```

### 3.2 第一个 LangGraph 应用

让我们构建一个简单的聊天机器人：

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

# 1. 定义状态
class ChatState(TypedDict):
    messages: list
    user_input: str
    ai_response: str

# 2. 定义节点
def chat_node(state: ChatState) -> dict:
    """处理用户输入并生成回复"""
    llm = ChatOpenAI(model="gpt-3.5-turbo")

    # 构建消息历史
    messages = state.get("messages", [])
    messages.append({"role": "user", "content": state["user_input"]})

    # 生成回复
    response = llm.invoke(messages)
    ai_response = response.content

    # 更新消息历史
    messages.append({"role": "assistant", "content": ai_response})

    return {
        "messages": messages,
        "ai_response": ai_response
    }

# 3. 构建图
workflow = StateGraph(ChatState)
workflow.add_node("chat", chat_node)
workflow.add_edge(START, "chat")
workflow.add_edge("chat", END)

# 4. 编译和运行
app = workflow.compile()

# 5. 使用
result = app.invoke({
    "user_input": "你好，请介绍一下自己",
    "messages": []
})

print(f"AI 回复: {result['ai_response']}")
```

### 3.3 添加条件逻辑

让我们增加一个情感分析节点：

```python
def sentiment_analysis(state: ChatState) -> dict:
    """分析用户输入的情感"""
    user_input = state["user_input"]

    # 简单的情感分析（实际应用中可使用专门的模型）
    positive_words = ["好", "棒", "喜欢", "开心", "满意"]
    negative_words = ["坏", "差", "讨厌", "生气", "不满"]

    sentiment = "neutral"
    if any(word in user_input for word in positive_words):
        sentiment = "positive"
    elif any(word in user_input for word in negative_words):
        sentiment = "negative"

    return {"sentiment": sentiment}

def route_by_sentiment(state: ChatState) -> str:
    """根据情感路由到不同的处理节点"""
    sentiment = state.get("sentiment", "neutral")
    return sentiment

def positive_response(state: ChatState) -> dict:
    """处理积极情感"""
    return {"ai_response": "很高兴听到您的积极反馈！😊"}

def negative_response(state: ChatState) -> dict:
    """处理消极情感"""
    return {"ai_response": "我理解您的感受，让我帮您解决问题。"}

def neutral_response(state: ChatState) -> dict:
    """处理中性情感"""
    return chat_node(state)  # 使用原来的聊天节点

# 更新状态定义
class EnhancedChatState(TypedDict):
    messages: list
    user_input: str
    ai_response: str
    sentiment: str

# 构建增强版图
workflow = StateGraph(EnhancedChatState)
workflow.add_node("sentiment", sentiment_analysis)
workflow.add_node("positive", positive_response)
workflow.add_node("negative", negative_response)
workflow.add_node("neutral", neutral_response)

# 添加边
workflow.add_edge(START, "sentiment")
workflow.add_conditional_edges(
    "sentiment",
    route_by_sentiment,
    {
        "positive": "positive",
        "negative": "negative",
        "neutral": "neutral"
    }
)
workflow.add_edge("positive", END)
workflow.add_edge("negative", END)
workflow.add_edge("neutral", END)

app = workflow.compile()
```

---

## 4. 状态管理

### 4.1 状态定义最佳实践

```python
from typing import Annotated, Optional
from typing_extensions import TypedDict
import operator

class ComprehensiveState(TypedDict):
    # 基础字段
    user_id: str
    session_id: str
    timestamp: str

    # 消息相关（使用 Annotated 定义合并策略）
    messages: Annotated[list, operator.add]  # 追加消息
    errors: Annotated[list, operator.add]    # 追加错误

    # 计数器（使用自定义合并函数）
    step_count: Annotated[int, lambda x, y: x + y]

    # 可选字段
    current_tool: Optional[str]
    intermediate_results: dict

    # 标志位
    is_complete: bool
    needs_human_input: bool
```

### 4.2 自定义状态合并

```python
def merge_dicts(existing: dict, new: dict) -> dict:
    """自定义字典合并策略"""
    result = existing.copy()
    result.update(new)
    return result

def max_value(existing: int, new: int) -> int:
    """保留最大值"""
    return max(existing, new)

class CustomState(TypedDict):
    config: Annotated[dict, merge_dicts]
    max_score: Annotated[int, max_value]
    data: Annotated[list, operator.add]
```

### 4.3 状态验证和类型检查

```python
from pydantic import BaseModel, Field
from typing import List

class ValidatedState(BaseModel):
    """使用 Pydantic 进行状态验证"""
    user_input: str = Field(..., min_length=1, max_length=1000)
    messages: List[dict] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)

    class Config:
        extra = "forbid"  # 禁止额外字段

def validated_node(state: dict) -> dict:
    """使用验证的节点"""
    # 验证输入状态
    validated_state = ValidatedState(**state)

    # 处理逻辑
    result = process_validated_data(validated_state)

    # 返回更新
    return {"confidence_score": result.confidence}
```

---

## 5. 节点和边

### 5.1 节点函数签名

LangGraph 支持多种节点函数签名：

```python
from langchain_core.runnables import RunnableConfig
from langgraph.types import Runtime

# 1. 基础签名：只接收状态
def basic_node(state: State) -> dict:
    return {"result": "processed"}

# 2. 带配置的节点
def node_with_config(state: State, config: RunnableConfig) -> dict:
    thread_id = config["configurable"]["thread_id"]
    return {"thread_id": thread_id}

# 3. 带运行时的节点
def node_with_runtime(state: State, runtime: Runtime) -> dict:
    user_id = runtime.context.user_id
    return {"user_id": user_id}

# 4. 完整签名
def full_node(state: State, config: RunnableConfig, runtime: Runtime) -> dict:
    return {
        "thread_id": config["configurable"]["thread_id"],
        "user_id": runtime.context.user_id,
        "processed": True
    }
```

### 5.2 条件边和路由

```python
def complex_routing(state: State) -> str:
    """复杂的路由逻辑"""
    if state.get("error"):
        return "error_handler"
    elif state.get("needs_approval"):
        return "human_review"
    elif state.get("confidence", 0) < 0.5:
        return "retry_node"
    else:
        return "success_node"

# 多条件路由
workflow.add_conditional_edges(
    "decision_node",
    complex_routing,
    {
        "error_handler": "handle_error",
        "human_review": "wait_for_human",
        "retry_node": "retry_processing",
        "success_node": "finalize"
    }
)
```

### 5.3 动态边和命令

```python
from langgraph.graph.command import Command
from typing import Literal

def dynamic_node(state: State) -> Command[Literal["node_a", "node_b"]]:
    """使用 Command 进行动态路由"""
    if state["condition"]:
        return Command(
            update={"status": "processing"},
            goto="node_a"
        )
    else:
        return Command(
            update={"status": "skipping"},
            goto="node_b"
        )
```

### 5.4 并行执行

```python
from langgraph.types import Send

def fan_out_node(state: State) -> list[Send]:
    """扇出到多个并行节点"""
    tasks = state["tasks"]
    return [
        Send("worker_node", {"task": task, "worker_id": i})
        for i, task in enumerate(tasks)
    ]

def worker_node(state: dict) -> dict:
    """工作节点处理单个任务"""
    task = state["task"]
    worker_id = state["worker_id"]

    result = process_task(task)

    return {
        "completed_tasks": [{
            "worker_id": worker_id,
            "task": task,
            "result": result
        }]
    }

# 添加并行节点
workflow.add_node("fan_out", fan_out_node)
workflow.add_node("worker", worker_node)
workflow.add_edge("fan_out", "worker")
```

---

## 6. 工作流构建

### 6.1 线性工作流

```python
def build_linear_workflow():
    """构建线性处理工作流"""

    class LinearState(TypedDict):
        input_data: str
        processed_data: str
        validated_data: str
        final_result: str

    def preprocess(state: LinearState) -> dict:
        data = state["input_data"].strip().lower()
        return {"processed_data": data}

    def validate(state: LinearState) -> dict:
        data = state["processed_data"]
        if len(data) > 0:
            return {"validated_data": data}
        else:
            raise ValueError("Invalid data")

    def finalize(state: LinearState) -> dict:
        data = state["validated_data"]
        result = f"Final: {data.upper()}"
        return {"final_result": result}

    workflow = StateGraph(LinearState)
    workflow.add_node("preprocess", preprocess)
    workflow.add_node("validate", validate)
    workflow.add_node("finalize", finalize)

    workflow.add_edge(START, "preprocess")
    workflow.add_edge("preprocess", "validate")
    workflow.add_edge("validate", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()
```

### 6.2 分支工作流

```python
def build_branching_workflow():
    """构建分支处理工作流"""

    class BranchState(TypedDict):
        input_type: str
        text_result: str
        image_result: str
        final_output: str

    def classify_input(state: BranchState) -> dict:
        # 模拟输入分类
        input_data = state.get("input_data", "")
        if "image" in input_data:
            return {"input_type": "image"}
        else:
            return {"input_type": "text"}

    def process_text(state: BranchState) -> dict:
        return {"text_result": "Processed text"}

    def process_image(state: BranchState) -> dict:
        return {"image_result": "Processed image"}

    def merge_results(state: BranchState) -> dict:
        if state.get("text_result"):
            output = state["text_result"]
        else:
            output = state["image_result"]
        return {"final_output": output}

    def route_by_type(state: BranchState) -> str:
        return state["input_type"]

    workflow = StateGraph(BranchState)
    workflow.add_node("classify", classify_input)
    workflow.add_node("process_text", process_text)
    workflow.add_node("process_image", process_image)
    workflow.add_node("merge", merge_results)

    workflow.add_edge(START, "classify")
    workflow.add_conditional_edges(
        "classify",
        route_by_type,
        {
            "text": "process_text",
            "image": "process_image"
        }
    )
    workflow.add_edge("process_text", "merge")
    workflow.add_edge("process_image", "merge")
    workflow.add_edge("merge", END)

    return workflow.compile()
```

### 6.3 循环工作流

```python
def build_iterative_workflow():
    """构建迭代优化工作流"""

    class IterativeState(TypedDict):
        current_solution: str
        iteration_count: int
        max_iterations: int
        quality_score: float
        is_complete: bool

    def improve_solution(state: IterativeState) -> dict:
        current = state["current_solution"]
        iteration = state["iteration_count"]

        # 模拟解决方案改进
        improved = f"{current}_v{iteration + 1}"
        quality = min(0.1 * (iteration + 1), 1.0)

        return {
            "current_solution": improved,
            "iteration_count": iteration + 1,
            "quality_score": quality
        }

    def check_completion(state: IterativeState) -> dict:
        is_complete = (
            state["quality_score"] >= 0.8 or
            state["iteration_count"] >= state["max_iterations"]
        )
        return {"is_complete": is_complete}

    def should_continue(state: IterativeState) -> str:
        if state["is_complete"]:
            return "end"
        else:
            return "continue"

    workflow = StateGraph(IterativeState)
    workflow.add_node("improve", improve_solution)
    workflow.add_node("check", check_completion)

    workflow.add_edge(START, "improve")
    workflow.add_edge("improve", "check")
    workflow.add_conditional_edges(
        "check",
        should_continue,
        {
            "continue": "improve",
            "end": END
        }
    )

    return workflow.compile()
```

---

## 7. 多智能体系统

### 7.1 Supervisor 模式

这是本项目使用的模式，通过监督者协调多个专门智能体：

```python
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent

def build_supervisor_system():
    """构建监督者多智能体系统"""

    # 1. 创建专门智能体
    research_agent = create_react_agent(
        model=llm,
        tools=research_tools,
        prompt="你是研究智能体，专门负责信息搜索...",
        name="research_agent"
    )

    math_agent = create_react_agent(
        model=llm,
        tools=math_tools,
        prompt="你是数学智能体，专门负责计算...",
        name="math_agent"
    )

    # 2. 创建监督者
    supervisor = create_supervisor(
        model=llm,
        agents=[research_agent, math_agent],
        prompt="""
        你是监督者，负责协调研究智能体和数学智能体：
        - 分析用户需求
        - 分配任务给合适的智能体
        - 整合结果
        """,
        add_handoff_back_messages=True,
        output_mode="full_history"
    )

    return supervisor.compile()
```

### 7.2 Peer-to-Peer 协作

智能体之间直接通信协作：

```python
class MultiAgentState(TypedDict):
    messages: Annotated[list, operator.add]
    current_speaker: str
    next_speaker: str
    task_complete: bool

def agent_a(state: MultiAgentState) -> dict:
    """智能体 A"""
    messages = state["messages"]

    # 处理逻辑
    response = "Agent A: 我已完成数据收集"

    return {
        "messages": [{"role": "agent_a", "content": response}],
        "next_speaker": "agent_b"
    }

def agent_b(state: MultiAgentState) -> dict:
    """智能体 B"""
    messages = state["messages"]

    # 处理逻辑
    response = "Agent B: 我已完成数据分析"

    return {
        "messages": [{"role": "agent_b", "content": response}],
        "task_complete": True
    }

def route_to_next_agent(state: MultiAgentState) -> str:
    if state.get("task_complete"):
        return "end"
    else:
        return state["next_speaker"]

# 构建 P2P 图
workflow = StateGraph(MultiAgentState)
workflow.add_node("agent_a", agent_a)
workflow.add_node("agent_b", agent_b)

workflow.add_edge(START, "agent_a")
workflow.add_conditional_edges(
    "agent_a",
    route_to_next_agent,
    {"agent_b": "agent_b", "end": END}
)
workflow.add_conditional_edges(
    "agent_b",
    route_to_next_agent,
    {"agent_a": "agent_a", "end": END}
)
```

### 7.3 层次化智能体团队

```python
def build_hierarchical_system():
    """构建层次化智能体系统"""

    # 底层工作智能体
    def create_worker_team():
        class WorkerState(TypedDict):
            task: str
            result: str

        def data_collector(state: WorkerState) -> dict:
            return {"result": f"收集到数据: {state['task']}"}

        def data_processor(state: WorkerState) -> dict:
            return {"result": f"处理了数据: {state['task']}"}

        worker_graph = StateGraph(WorkerState)
        worker_graph.add_node("collect", data_collector)
        worker_graph.add_node("process", data_processor)
        worker_graph.add_edge(START, "collect")
        worker_graph.add_edge("collect", "process")
        worker_graph.add_edge("process", END)

        return worker_graph.compile()

    # 中层管理智能体
    def create_manager():
        class ManagerState(TypedDict):
            tasks: list
            results: Annotated[list, operator.add]

        def delegate_tasks(state: ManagerState) -> list[Send]:
            return [
                Send("worker_team", {"task": task})
                for task in state["tasks"]
            ]

        manager_graph = StateGraph(ManagerState)
        manager_graph.add_node("delegate", delegate_tasks)
        manager_graph.add_node("worker_team", create_worker_team())
        manager_graph.add_edge(START, "delegate")
        manager_graph.add_edge("delegate", "worker_team")
        manager_graph.add_edge("worker_team", END)

        return manager_graph.compile()

    return create_manager()
```

---

## 8. 高级特性

### 8.1 检查点和持久化

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 1. 内存检查点（开发测试）
memory_saver = MemorySaver()
app = workflow.compile(checkpointer=memory_saver)

# 2. SQLite 检查点（生产环境）
sqlite_saver = SqliteSaver.from_conn_string("checkpoints.db")
app = workflow.compile(checkpointer=sqlite_saver)

# 3. 使用检查点
config = {"configurable": {"thread_id": "user_123"}}

# 第一次调用
result1 = app.invoke({"input": "Hello"}, config)

# 第二次调用（会恢复之前的状态）
result2 = app.invoke({"input": "Continue"}, config)
```

### 8.2 人工干预

```python
from langgraph.graph import interrupt

def human_review_node(state: State) -> dict:
    """需要人工审核的节点"""
    if state.get("needs_review"):
        # 触发中断，等待人工输入
        interrupt("需要人工审核当前结果")

    return {"status": "reviewed"}

# 编译时启用中断
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review_node"]  # 在此节点前中断
)

# 运行到中断点
result = app.invoke(input_data, config)

# 人工审核后继续
app.update_state(config, {"approval": "approved"})
final_result = app.invoke(None, config)
```

### 8.3 流式处理

```python
# 1. 同步流式处理
for chunk in app.stream(input_data, config):
    print(f"节点 {chunk.keys()} 完成")
    print(f"输出: {chunk}")

# 2. 异步流式处理
async def async_stream_example():
    async for chunk in app.astream(input_data, config):
        print(f"异步处理: {chunk}")

# 3. 流式模式
for chunk in app.stream(input_data, config, stream_mode="values"):
    print(f"当前状态: {chunk}")

for chunk in app.stream(input_data, config, stream_mode="updates"):
    print(f"状态更新: {chunk}")
```

### 8.4 错误处理和重试

```python
import tenacity
from langgraph.errors import GraphRecursionError

def robust_node(state: State) -> dict:
    """带错误处理的节点"""
    try:
        result = risky_operation(state["input"])
        return {"result": result, "error": None}
    except Exception as e:
        return {"result": None, "error": str(e)}

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=10)
)
def retry_node(state: State) -> dict:
    """带重试机制的节点"""
    if state.get("retry_count", 0) >= 3:
        raise Exception("超过最大重试次数")

    try:
        result = unreliable_operation()
        return {"result": result}
    except Exception:
        return {"retry_count": state.get("retry_count", 0) + 1}

# 递归限制
app = workflow.compile(
    checkpointer=checkpointer,
    recursion_limit=100  # 防止无限循环
)
```

### 8.5 缓存机制

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.types import CachePolicy
import time

def expensive_computation(state: State) -> dict:
    """耗时计算节点"""
    time.sleep(2)  # 模拟耗时操作
    return {"result": state["input"] * 2}

# 添加缓存策略
workflow.add_node(
    "expensive_node",
    expensive_computation,
    cache_policy=CachePolicy(ttl=300)  # 5分钟缓存
)

# 编译时启用缓存
app = workflow.compile(cache=InMemoryCache())

# 第一次调用（慢）
result1 = app.invoke({"input": 5})

# 第二次调用（快，使用缓存）
result2 = app.invoke({"input": 5})
```

---

## 9. 实战案例

### 9.1 智能客服系统

```python
def build_customer_service_bot():
    """构建智能客服系统"""

    class CustomerServiceState(TypedDict):
        user_message: str
        intent: str
        entities: dict
        response: str
        escalate_to_human: bool
        conversation_history: Annotated[list, operator.add]

    def intent_recognition(state: CustomerServiceState) -> dict:
        """意图识别"""
        message = state["user_message"]

        # 简化的意图识别
        if "退款" in message or "refund" in message.lower():
            intent = "refund_request"
        elif "订单" in message or "order" in message.lower():
            intent = "order_inquiry"
        elif "技术" in message or "technical" in message.lower():
            intent = "technical_support"
        else:
            intent = "general_inquiry"

        return {"intent": intent}

    def handle_refund(state: CustomerServiceState) -> dict:
        """处理退款请求"""
        return {
            "response": "我来帮您处理退款申请。请提供您的订单号。",
            "escalate_to_human": False
        }

    def handle_order_inquiry(state: CustomerServiceState) -> dict:
        """处理订单查询"""
        return {
            "response": "请提供您的订单号，我来查询订单状态。",
            "escalate_to_human": False
        }

    def handle_technical_support(state: CustomerServiceState) -> dict:
        """处理技术支持"""
        return {
            "response": "技术问题比较复杂，我为您转接技术专家。",
            "escalate_to_human": True
        }

    def handle_general(state: CustomerServiceState) -> dict:
        """处理一般咨询"""
        return {
            "response": "感谢您的咨询，我来为您解答。",
            "escalate_to_human": False
        }

    def route_by_intent(state: CustomerServiceState) -> str:
        intent_map = {
            "refund_request": "handle_refund",
            "order_inquiry": "handle_order",
            "technical_support": "handle_technical",
            "general_inquiry": "handle_general"
        }
        return intent_map.get(state["intent"], "handle_general")

    # 构建工作流
    workflow = StateGraph(CustomerServiceState)
    workflow.add_node("intent_recognition", intent_recognition)
    workflow.add_node("handle_refund", handle_refund)
    workflow.add_node("handle_order", handle_order_inquiry)
    workflow.add_node("handle_technical", handle_technical_support)
    workflow.add_node("handle_general", handle_general)

    workflow.add_edge(START, "intent_recognition")
    workflow.add_conditional_edges(
        "intent_recognition",
        route_by_intent,
        {
            "handle_refund": "handle_refund",
            "handle_order": "handle_order",
            "handle_technical": "handle_technical",
            "handle_general": "handle_general"
        }
    )

    # 所有处理节点都连接到结束
    for node in ["handle_refund", "handle_order", "handle_technical", "handle_general"]:
        workflow.add_edge(node, END)

    return workflow.compile()
```

### 9.2 文档处理管道

```python
def build_document_pipeline():
    """构建文档处理管道"""

    class DocumentState(TypedDict):
        document_path: str
        document_type: str
        extracted_text: str
        processed_chunks: list
        embeddings: list
        summary: str
        keywords: list

    def detect_document_type(state: DocumentState) -> dict:
        """检测文档类型"""
        path = state["document_path"]
        if path.endswith('.pdf'):
            doc_type = "pdf"
        elif path.endswith('.docx'):
            doc_type = "word"
        elif path.endswith('.txt'):
            doc_type = "text"
        else:
            doc_type = "unknown"

        return {"document_type": doc_type}

    def extract_text(state: DocumentState) -> dict:
        """提取文本内容"""
        doc_type = state["document_type"]
        path = state["document_path"]

        # 根据文档类型提取文本
        if doc_type == "pdf":
            text = extract_pdf_text(path)
        elif doc_type == "word":
            text = extract_word_text(path)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()

        return {"extracted_text": text}

    def chunk_text(state: DocumentState) -> dict:
        """文本分块"""
        text = state["extracted_text"]

        # 简单的分块策略
        chunks = []
        words = text.split()
        chunk_size = 200

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        return {"processed_chunks": chunks}

    def generate_embeddings(state: DocumentState) -> dict:
        """生成向量嵌入"""
        chunks = state["processed_chunks"]

        # 使用嵌入模型生成向量
        embeddings = []
        for chunk in chunks:
            # 这里应该调用实际的嵌入模型
            embedding = generate_embedding(chunk)
            embeddings.append(embedding)

        return {"embeddings": embeddings}

    def generate_summary(state: DocumentState) -> dict:
        """生成摘要"""
        text = state["extracted_text"]

        # 使用 LLM 生成摘要
        llm = ChatOpenAI(model="gpt-3.5-turbo")
        summary_prompt = f"请为以下文档生成简洁的摘要：\n\n{text[:2000]}..."

        summary = llm.invoke([{"role": "user", "content": summary_prompt}]).content

        return {"summary": summary}

    def extract_keywords(state: DocumentState) -> dict:
        """提取关键词"""
        text = state["extracted_text"]

        # 简单的关键词提取
        words = text.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # 过滤短词
                word_freq[word] = word_freq.get(word, 0) + 1

        # 取频率最高的10个词作为关键词
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        keywords = [word for word, freq in keywords]

        return {"keywords": keywords}

    # 构建管道
    workflow = StateGraph(DocumentState)
    workflow.add_node("detect_type", detect_document_type)
    workflow.add_node("extract_text", extract_text)
    workflow.add_node("chunk_text", chunk_text)
    workflow.add_node("generate_embeddings", generate_embeddings)
    workflow.add_node("generate_summary", generate_summary)
    workflow.add_node("extract_keywords", extract_keywords)

    # 线性处理流程
    workflow.add_edge(START, "detect_type")
    workflow.add_edge("detect_type", "extract_text")
    workflow.add_edge("extract_text", "chunk_text")

    # 并行处理嵌入、摘要和关键词
    workflow.add_edge("chunk_text", "generate_embeddings")
    workflow.add_edge("chunk_text", "generate_summary")
    workflow.add_edge("chunk_text", "extract_keywords")

    workflow.add_edge("generate_embeddings", END)
    workflow.add_edge("generate_summary", END)
    workflow.add_edge("extract_keywords", END)

    return workflow.compile()
```

---

## 10. 最佳实践

### 10.1 性能优化

```python
# 1. 使用连接池
from functools import lru_cache

@lru_cache(maxsize=10)
def get_llm_model(model_name: str):
    """缓存 LLM 模型实例"""
    return ChatOpenAI(model=model_name)

# 2. 批处理
def batch_process_node(state: State) -> dict:
    """批量处理多个项目"""
    items = state["items"]
    batch_size = 10

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = process_batch(batch)
        results.extend(batch_results)

    return {"results": results}

# 3. 异步处理
import asyncio

async def async_node(state: State) -> dict:
    """异步节点处理"""
    tasks = [
        async_operation_1(state["data"]),
        async_operation_2(state["data"]),
        async_operation_3(state["data"])
    ]

    results = await asyncio.gather(*tasks)

    return {"async_results": results}
```

### 10.2 错误处理策略

```python
def robust_workflow_design():
    """健壮的工作流设计"""

    class RobustState(TypedDict):
        input_data: str
        processed_data: str
        error_count: int
        max_retries: int
        last_error: str
        success: bool

    def safe_processing_node(state: RobustState) -> dict:
        """安全的处理节点"""
        try:
            result = risky_operation(state["input_data"])
            return {
                "processed_data": result,
                "success": True,
                "error_count": 0
            }
        except Exception as e:
            error_count = state.get("error_count", 0) + 1
            return {
                "error_count": error_count,
                "last_error": str(e),
                "success": False
            }

    def error_recovery_node(state: RobustState) -> dict:
        """错误恢复节点"""
        if state["error_count"] < state["max_retries"]:
            # 尝试恢复
            return {"input_data": fallback_data(state["input_data"])}
        else:
            # 彻底失败
            return {"success": False, "final_error": "超过最大重试次数"}

    def should_retry(state: RobustState) -> str:
        if state["success"]:
            return "success"
        elif state["error_count"] < state["max_retries"]:
            return "retry"
        else:
            return "failed"

    workflow = StateGraph(RobustState)
    workflow.add_node("process", safe_processing_node)
    workflow.add_node("recover", error_recovery_node)

    workflow.add_edge(START, "process")
    workflow.add_conditional_edges(
        "process",
        should_retry,
        {
            "success": END,
            "retry": "recover",
            "failed": END
        }
    )
    workflow.add_edge("recover", "process")

    return workflow.compile()
```

### 10.3 监控和日志

```python
import logging
import time
from functools import wraps

def monitor_node_performance(func):
    """节点性能监控装饰器"""
    @wraps(func)
    def wrapper(state, *args, **kwargs):
        start_time = time.time()
        node_name = func.__name__

        try:
            result = func(state, *args, **kwargs)
            duration = time.time() - start_time

            logging.info(f"节点 {node_name} 执行成功，耗时 {duration:.2f}s")

            # 添加性能指标到状态
            if isinstance(result, dict):
                result["_performance"] = {
                    "node": node_name,
                    "duration": duration,
                    "status": "success"
                }

            return result

        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"节点 {node_name} 执行失败，耗时 {duration:.2f}s，错误: {e}")

            return {
                "_performance": {
                    "node": node_name,
                    "duration": duration,
                    "status": "error",
                    "error": str(e)
                }
            }

    return wrapper

@monitor_node_performance
def monitored_node(state: State) -> dict:
    """被监控的节点"""
    # 业务逻辑
    return {"result": "processed"}
```

### 10.4 测试策略

```python
import pytest
from unittest.mock import Mock, patch

def test_node_function():
    """测试单个节点函数"""
    # 准备测试状态
    test_state = {
        "input_data": "test input",
        "step_count": 0
    }

    # 调用节点函数
    result = my_node(test_state)

    # 验证结果
    assert "processed_data" in result
    assert result["step_count"] == 1

def test_workflow_integration():
    """测试工作流集成"""
    # 创建测试工作流
    app = build_test_workflow()

    # 准备测试输入
    test_input = {"user_input": "test message"}

    # 执行工作流
    result = app.invoke(test_input)

    # 验证最终结果
    assert result["final_output"] is not None
    assert "error" not in result

@patch('external_api.call')
def test_node_with_external_dependency(mock_api_call):
    """测试依赖外部服务的节点"""
    # 模拟外部 API 响应
    mock_api_call.return_value = {"status": "success", "data": "mocked data"}

    # 测试节点
    state = {"api_input": "test"}
    result = api_dependent_node(state)

    # 验证调用和结果
    mock_api_call.assert_called_once()
    assert result["api_result"] == "mocked data"

def test_error_handling():
    """测试错误处理"""
    # 准备会导致错误的状态
    error_state = {"invalid_input": None}

    # 执行节点（应该优雅处理错误）
    result = error_prone_node(error_state)

    # 验证错误被正确处理
    assert "error" in result
    assert result["error"] is not None
```

### 10.5 部署和运维

```python
# 1. 配置管理
import os
from dataclasses import dataclass

@dataclass
class AppConfig:
    llm_model: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    timeout: int = int(os.getenv("TIMEOUT", "30"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

# 2. 健康检查
def health_check_endpoint():
    """健康检查端点"""
    try:
        # 测试关键组件
        test_state = {"test": "data"}
        app.invoke(test_state, {"configurable": {"thread_id": "health_check"}})
        return {"status": "healthy", "timestamp": time.time()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}

# 3. 指标收集
class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0
        }

    def record_request(self, success: bool, response_time: float):
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1

        # 更新平均响应时间
        total_time = self.metrics["average_response_time"] * (self.metrics["total_requests"] - 1)
        self.metrics["average_response_time"] = (total_time + response_time) / self.metrics["total_requests"]

# 4. 优雅关闭
import signal
import sys

class GracefulShutdown:
    def __init__(self, app):
        self.app = app
        self.shutdown = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logging.info(f"收到信号 {signum}，开始优雅关闭...")
        self.shutdown = True
        # 等待当前请求完成
        # 清理资源
        sys.exit(0)
```

---

## 总结

LangGraph 是一个强大的框架，用于构建复杂的、有状态的 AI 应用。通过本教程，你应该已经掌握了：

### 核心概念
- **图结构**：节点、边、状态的关系
- **状态管理**：类型安全的状态定义和合并策略
- **控制流**：条件路由、循环、并行执行

### 实用技能
- **工作流设计**：线性、分支、循环模式
- **多智能体协作**：Supervisor、P2P、层次化模式
- **错误处理**：重试、恢复、优雅降级

### 高级特性
- **持久化**：检查点、状态恢复
- **人工干预**：中断、审核、继续
- **性能优化**：缓存、批处理、异步

### 生产实践
- **监控日志**：性能跟踪、错误监控
- **测试策略**：单元测试、集成测试
- **部署运维**：配置管理、健康检查

LangGraph 为构建下一代 AI 应用提供了坚实的基础。结合本项目的实战案例，你现在可以开始构建自己的多智能体系统了！

---

## 附录：常用 API 参考

### A.1 StateGraph 核心 API

```python
from langgraph.graph import StateGraph, START, END

# 创建图
graph = StateGraph(StateClass)

# 添加节点
graph.add_node("node_name", node_function)

# 添加边
graph.add_edge("start_node", "end_node")
graph.add_edge(START, "first_node")
graph.add_edge("last_node", END)

# 添加条件边
graph.add_conditional_edges(
    "source_node",
    condition_function,
    {
        "condition_a": "target_node_a",
        "condition_b": "target_node_b"
    }
)

# 编译图
app = graph.compile(
    checkpointer=checkpointer,  # 可选：检查点保存器
    interrupt_before=["node1"],  # 可选：在指定节点前中断
    interrupt_after=["node2"],   # 可选：在指定节点后中断
)
```

### A.2 执行方法

```python
# 同步执行
result = app.invoke(input_data, config)

# 异步执行
result = await app.ainvoke(input_data, config)

# 流式执行
for chunk in app.stream(input_data, config):
    print(chunk)

# 异步流式执行
async for chunk in app.astream(input_data, config):
    print(chunk)

# 批量执行
results = app.batch([input1, input2, input3], config)

# 异步批量执行
results = await app.abatch([input1, input2, input3], config)
```

### A.3 配置选项

```python
config = {
    "configurable": {
        "thread_id": "user_123",        # 线程 ID
        "checkpoint_id": "checkpoint_1", # 检查点 ID
    },
    "recursion_limit": 100,             # 递归限制
    "tags": ["production", "v1.0"],     # 标签
    "metadata": {"user": "john"},       # 元数据
}
```

### A.4 状态管理

```python
from typing import Annotated
import operator

# 基础状态
class BasicState(TypedDict):
    field1: str
    field2: int

# 带合并策略的状态
class AdvancedState(TypedDict):
    messages: Annotated[list, operator.add]  # 列表追加
    counters: Annotated[dict, merge_dicts]   # 字典合并
    max_value: Annotated[int, max]           # 取最大值

# 自定义合并函数
def merge_dicts(existing: dict, new: dict) -> dict:
    result = existing.copy()
    result.update(new)
    return result
```

### A.5 检查点和持久化

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# 内存检查点
memory_saver = MemorySaver()

# SQLite 检查点
sqlite_saver = SqliteSaver.from_conn_string("checkpoints.db")

# 使用检查点
app = graph.compile(checkpointer=sqlite_saver)

# 获取状态历史
history = app.get_state_history(config)
for state in history:
    print(state.values)

# 更新状态
app.update_state(config, {"field": "new_value"})
```

### A.6 人工干预

```python
from langgraph.graph import interrupt

def human_node(state: State) -> dict:
    # 触发中断
    interrupt("需要人工审核")
    return {"status": "waiting"}

# 编译时设置中断点
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_node"]
)

# 执行到中断点
result = app.invoke(input_data, config)

# 检查是否中断
if app.get_state(config).next:
    print("工作流已中断，等待人工输入")

# 继续执行
app.update_state(config, {"approval": "approved"})
final_result = app.invoke(None, config)
```

### A.7 错误处理

```python
from langgraph.errors import GraphRecursionError, GraphInterrupt

try:
    result = app.invoke(input_data, config)
except GraphRecursionError:
    print("超过递归限制")
except GraphInterrupt as e:
    print(f"工作流中断: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

### A.8 工具集成

```python
from langgraph.prebuilt import create_react_agent, ToolNode

# 创建 ReAct 智能体
def my_tool(input: str) -> str:
    """工具描述"""
    return f"处理结果: {input}"

agent = create_react_agent(
    model=llm,
    tools=[my_tool],
    prompt="你是一个有用的助手"
)

# 工具节点
tool_node = ToolNode([my_tool])
graph.add_node("tools", tool_node)
```

### A.9 多智能体

```python
from langgraph_supervisor import create_supervisor

# 创建监督者
supervisor = create_supervisor(
    model=llm,
    agents=[agent1, agent2, agent3],
    prompt="监督者提示词",
    add_handoff_back_messages=True,
    output_mode="full_history"
)

# 编译监督者图
supervisor_app = supervisor.compile()
```

### A.10 调试和可视化

```python
# 打印图结构
print(app.get_graph().draw_ascii())

# 获取图的 Mermaid 表示
mermaid_code = app.get_graph().draw_mermaid()

# 可视化（需要安装 graphviz）
app.get_graph().draw_png("workflow.png")

# 调试信息
state = app.get_state(config)
print(f"当前状态: {state.values}")
print(f"下一个节点: {state.next}")
print(f"任务: {state.tasks}")
```

---

## 参考资源

- [LangGraph 官方文档](https://langchain-ai.github.io/langgraph/)
- [LangGraph GitHub](https://github.com/langchain-ai/langgraph)
- [LangChain 文档](https://python.langchain.com/)
- [本项目示例代码](../example/graph.py)
- [LangGraph 教程集合](https://langchain-ai.github.io/langgraph/tutorials/)
- [LangGraph 概念指南](https://langchain-ai.github.io/langgraph/concepts/)
- [LangGraph API 参考](https://langchain-ai.github.io/langgraph/reference/)
