# 17. 多智能体系统教学

## 🎯 学习目标

通过这个教程，你将学会：
- 多智能体系统的设计原理
- Supervisor 模式的实现方法
- 智能体间的协作和通信
- 任务分配和路由策略

## 📚 核心概念

### 1. 什么是多智能体系统？

多智能体系统是由**多个专门化智能体协作**完成复杂任务的系统：

```
用户请求 → 监督者分析 → 选择专门智能体 → 执行任务 → 返回结果
```

**系统优势：**
- **专业化**：每个智能体专注特定领域
- **可扩展**：易于添加新的智能体
- **容错性**：单个智能体故障不影响整体
- **并行处理**：多个智能体可同时工作

### 2. Supervisor 模式

Supervisor 模式是一种**中心化协调**的多智能体架构：

```python
class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    task_complete: bool
```

**核心组件：**
- **监督者**：分析任务，选择合适的智能体
- **专门智能体**：执行特定类型的任务
- **路由逻辑**：决定任务流向
- **状态管理**：协调智能体间的信息传递

### 3. 智能体专业化

每个智能体都有特定的工具和提示：

```python
# 研究智能体
research_agent = create_react_agent(
    model=llm,
    tools=[search_information],
    prompt="你是研究智能体，专门负责信息搜索和数据收集。"
)

# 数学智能体
math_agent = create_react_agent(
    model=llm,
    tools=[calculate_math],
    prompt="你是数学智能体，专门负责数学计算和数值分析。"
)
```

## 🔍 代码详细解析

### 监督者节点实现

```python
def supervisor_node(state: SupervisorState):
    """监督者节点"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {"next_agent": "END", "task_complete": True}

    user_content = last_message.content.lower()

    # 任务类型分析和智能体分配
    if any(keyword in user_content for keyword in ["搜索", "查找", "信息"]):
        next_agent = "research_agent"
    elif any(keyword in user_content for keyword in ["计算", "数学"]):
        next_agent = "math_agent"
    elif any(keyword in user_content for keyword in ["写", "创作", "生成"]):
        next_agent = "content_agent"
    elif any(keyword in user_content for keyword in ["分析", "统计", "数据"]):
        next_agent = "analysis_agent"
    else:
        next_agent = "research_agent"  # 默认智能体

    # 添加监督者的分析消息
    supervisor_message = f"[监督者] 分析任务类型，分配给 {next_agent}"

    return {
        "messages": [{"role": "assistant", "content": supervisor_message}],
        "next_agent": next_agent,
        "task_complete": False
    }
```

### 专门智能体工具

```python
@tool
def search_information(query: str) -> str:
    """搜索信息工具"""
    search_results = {
        "天气": "今天天气晴朗，温度适宜",
        "新闻": "今日重要新闻：科技发展迅速",
        "股票": "股市今日表现平稳"
    }

    for key, result in search_results.items():
        if key in query:
            return f"搜索结果：{result}"

    return f"搜索'{query}'的结果：相关信息已找到"

@tool
def calculate_math(expression: str) -> str:
    """数学计算工具"""
    try:
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression)
        return f"计算结果：{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"

@tool
def generate_content(topic: str) -> str:
    """内容生成工具"""
    content_templates = {
        "故事": f"从前有一个关于{topic}的故事...",
        "诗歌": f"关于{topic}的诗歌：\n春风{topic}绿江南岸...",
        "文章": f"{topic}相关文章：\n这是一篇关于{topic}的深度分析..."
    }

    for key, template in content_templates.items():
        if key in topic:
            return template

    return f"已生成关于'{topic}'的内容"
```

### 路由逻辑

```python
def route_to_agent(state: SupervisorState) -> Literal["research_agent", "math_agent", "content_agent", "analysis_agent", "END"]:
    """路由到指定智能体"""
    if state.get("task_complete"):
        return "END"
    return state["next_agent"]

# 构建监督者图
supervisor_builder = StateGraph(SupervisorState)

# 添加节点
supervisor_builder.add_node("supervisor", supervisor_node)
supervisor_builder.add_node("research_agent", research_node)
supervisor_builder.add_node("math_agent", math_node)
supervisor_builder.add_node("content_agent", content_node)
supervisor_builder.add_node("analysis_agent", analysis_node)

# 添加条件边
supervisor_builder.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "research_agent": "research_agent",
        "math_agent": "math_agent",
        "content_agent": "content_agent",
        "analysis_agent": "analysis_agent",
        "END": END
    }
)
```

## 🚀 运行演示

### 基础多智能体演示

```python
def run_supervisor_demo():
    """运行监督者模式演示"""
    print("监督者模式多智能体演示启动！")
    print("监督者会分析任务并分配给合适的专门智能体：")
    print("- 研究智能体：信息搜索")
    print("- 数学智能体：数学计算")
    print("- 内容智能体：内容创作")
    print("- 分析智能体：数据分析")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        try:
            result = supervisor_graph.invoke({
                "messages": [{"role": "user", "content": user_input}]
            })

            # 输出所有消息
            for message in result["messages"]:
                if message.get("role") == "assistant":
                    content = message.get("content", "")
                    if content.startswith("[监督者]"):
                        print(f"🎯 {content}")
                    else:
                        print(f"🤖 智能体回复: {content}")

        except Exception as e:
            print(f"处理错误: {e}")
```

### 预期输出

```
用户: 搜索今天的天气信息
🎯 [监督者] 分析任务类型，分配给 research_agent
🤖 智能体回复: 根据搜索结果，今天天气晴朗，温度适宜。

用户: 计算 15 + 27 * 3
🎯 [监督者] 分析任务类型，分配给 math_agent
🤖 智能体回复: 计算结果：15 + 27 * 3 = 96

用户: 写一个关于春天的故事
🎯 [监督者] 分析任务类型，分配给 content_agent
🤖 智能体回复: 从前有一个关于春天的故事...
```

## 🎯 高级多智能体模式

### 1. 智能体能力测试

```python
def test_supervisor_routing():
    """测试监督者路由"""
    test_cases = [
        ("搜索今天的天气信息", "research_agent"),
        ("计算 15 + 27 * 3", "math_agent"),
        ("写一个关于春天的故事", "content_agent"),
        ("分析数据：1,2,3,4,5", "analysis_agent"),
    ]

    for user_input, expected_agent in test_cases:
        print(f"\n测试输入: {user_input}")
        print(f"期望智能体: {expected_agent}")

        # 只运行监督者节点来测试路由
        result = supervisor_node({
            "messages": [{"role": "user", "content": user_input}],
            "next_agent": "",
            "task_complete": False
        })

        actual_agent = result["next_agent"]
        print(f"实际智能体: {actual_agent}")
        print(f"路由{'✅ 正确' if actual_agent == expected_agent else '❌ 错误'}")
```

### 2. 多步骤工作流

```python
def demo_multi_step_workflow():
    """演示多步骤工作流"""
    workflow_steps = [
        "搜索关于人工智能的最新信息",
        "分析数据：10,20,30,40,50",
        "计算平均值的两倍",
        "写一篇关于AI发展的简短文章"
    ]

    print("执行多步骤工作流:")
    for i, step in enumerate(workflow_steps, 1):
        print(f"\n=== 步骤 {i}: {step} ===")

        result = supervisor_graph.invoke({
            "messages": [{"role": "user", "content": step}]
        })

        # 输出结果
        for message in result["messages"]:
            if message.get("role") == "assistant":
                content = message.get("content", "")
                if content.startswith("[监督者]"):
                    print(f"🎯 {content}")
                else:
                    print(f"🤖 {content}")
```

### 3. 智能体专业化验证

```python
def demo_agent_specialization():
    """演示智能体专业化"""
    agent_tests = [
        {
            "agent": "research_agent",
            "name": "研究智能体",
            "tests": ["搜索天气信息", "查找新闻", "获取股票信息"]
        },
        {
            "agent": "math_agent",
            "name": "数学智能体",
            "tests": ["计算 2+3", "计算 10*5", "计算 (8-3)*4"]
        },
        {
            "agent": "content_agent",
            "name": "内容智能体",
            "tests": ["写一个故事", "创作诗歌", "生成文章"]
        }
    ]

    for agent_info in agent_tests:
        print(f"\n=== {agent_info['name']} 专业能力测试 ===")

        for test in agent_info["tests"]:
            print(f"\n测试: {test}")

            result = supervisor_graph.invoke({
                "messages": [{"role": "user", "content": test}]
            })

            # 检查是否路由到正确的智能体
            supervisor_msg = result["messages"][0].content if result["messages"] else ""
            if agent_info["agent"] in supervisor_msg:
                print("✅ 正确路由")
            else:
                print("❌ 路由错误")
```

## 🎯 实践练习

### 练习1：添加新智能体

```python
@tool
def translate_text(text: str, target_language: str = "英文") -> str:
    """翻译文本工具"""
    # 简单的翻译模拟
    translations = {
        "你好": {"英文": "Hello", "日文": "こんにちは"},
        "谢谢": {"英文": "Thank you", "日文": "ありがとう"},
        "再见": {"英文": "Goodbye", "日文": "さようなら"}
    }

    if text in translations and target_language in translations[text]:
        return f"翻译结果：{text} -> {translations[text][target_language]}"

    return f"已将'{text}'翻译为{target_language}"

# 创建翻译智能体
translation_agent = create_react_agent(
    model=llm,
    tools=[translate_text],
    prompt="你是翻译智能体，专门负责文本翻译。"
)

def translation_node(state: SupervisorState):
    """翻译智能体节点"""
    result = translation_agent.invoke(state)
    return {
        "messages": result["messages"],
        "task_complete": True
    }

# 更新监督者逻辑
def enhanced_supervisor_node(state: SupervisorState):
    """增强的监督者节点"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {"next_agent": "END", "task_complete": True}

    user_content = last_message.content.lower()

    # 添加翻译任务检测
    if any(keyword in user_content for keyword in ["翻译", "translate"]):
        next_agent = "translation_agent"
    elif any(keyword in user_content for keyword in ["搜索", "查找"]):
        next_agent = "research_agent"
    # ... 其他逻辑
    else:
        next_agent = "research_agent"

    supervisor_message = f"[监督者] 分析任务类型，分配给 {next_agent}"

    return {
        "messages": [{"role": "assistant", "content": supervisor_message}],
        "next_agent": next_agent,
        "task_complete": False
    }
```

### 练习2：智能体协作

```python
def demo_agent_collaboration():
    """演示智能体协作"""
    # 复杂任务：需要多个智能体协作
    complex_task = "搜索Python编程的信息，然后计算学习时间，最后写一个学习计划"

    print(f"复杂任务: {complex_task}")

    # 分解任务
    subtasks = [
        "搜索Python编程的相关信息",
        "计算学习Python需要的时间（假设每天2小时）",
        "根据以上信息写一个Python学习计划"
    ]

    results = []
    for i, subtask in enumerate(subtasks, 1):
        print(f"\n--- 子任务 {i}: {subtask} ---")

        result = supervisor_graph.invoke({
            "messages": [{"role": "user", "content": subtask}]
        })

        # 收集结果
        for message in result["messages"]:
            if message.get("role") == "assistant" and not message.get("content", "").startswith("[监督者]"):
                results.append(message.get("content", ""))
                print(f"结果: {message.get('content', '')}")

    # 汇总所有结果
    print(f"\n=== 任务完成汇总 ===")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result}")
```

### 练习3：智能体性能监控

```python
import time

class AgentPerformanceMonitor:
    """智能体性能监控器"""

    def __init__(self):
        self.agent_stats = {}

    def record_execution(self, agent_name: str, execution_time: float, success: bool):
        """记录智能体执行情况"""
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name] = {
                "total_calls": 0,
                "total_time": 0,
                "success_count": 0,
                "failure_count": 0
            }

        stats = self.agent_stats[agent_name]
        stats["total_calls"] += 1
        stats["total_time"] += execution_time

        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1

    def get_performance_report(self) -> str:
        """获取性能报告"""
        report = "=== 智能体性能报告 ===\n"

        for agent_name, stats in self.agent_stats.items():
            avg_time = stats["total_time"] / stats["total_calls"] if stats["total_calls"] > 0 else 0
            success_rate = stats["success_count"] / stats["total_calls"] if stats["total_calls"] > 0 else 0

            report += f"\n{agent_name}:\n"
            report += f"  总调用次数: {stats['total_calls']}\n"
            report += f"  平均执行时间: {avg_time:.2f}秒\n"
            report += f"  成功率: {success_rate:.2%}\n"

        return report

# 使用监控器
monitor = AgentPerformanceMonitor()

def monitored_agent_call(agent_name: str, agent_func, state):
    """带监控的智能体调用"""
    start_time = time.time()
    success = True

    try:
        result = agent_func(state)
        return result
    except Exception as e:
        success = False
        print(f"智能体 {agent_name} 执行失败: {e}")
        return {"messages": [{"role": "assistant", "content": f"执行失败: {e}"}], "task_complete": True}
    finally:
        execution_time = time.time() - start_time
        monitor.record_execution(agent_name, execution_time, success)
```

## 🔧 常见问题

### Q1: 如何处理智能体选择错误？

**答：** 实现智能体能力验证和回退机制：

```python
def validate_agent_capability(agent_name: str, task: str) -> bool:
    """验证智能体能力"""
    capabilities = {
        "research_agent": ["搜索", "查找", "信息"],
        "math_agent": ["计算", "数学", "数值"],
        "content_agent": ["写", "创作", "生成"]
    }

    if agent_name in capabilities:
        keywords = capabilities[agent_name]
        return any(keyword in task.lower() for keyword in keywords)

    return False

def smart_supervisor_node(state: SupervisorState):
    """智能监督者节点"""
    # 原有逻辑...
    selected_agent = "research_agent"  # 假设选择结果

    # 验证选择
    task = state["messages"][-1].content
    if not validate_agent_capability(selected_agent, task):
        print(f"警告：{selected_agent} 可能不适合处理任务：{task}")
        selected_agent = "research_agent"  # 回退到默认智能体

    return {
        "next_agent": selected_agent,
        "task_complete": False
    }
```

### Q2: 如何实现智能体间的信息传递？

**答：** 使用共享状态和消息传递：

```python
class CollaborativeState(TypedDict):
    messages: Annotated[list, add_messages]
    shared_context: dict
    agent_results: dict
    current_agent: str

def collaborative_agent_node(state: CollaborativeState):
    """协作智能体节点"""
    # 获取其他智能体的结果
    previous_results = state.get("agent_results", {})
    shared_context = state.get("shared_context", {})

    # 使用共享信息执行任务
    enhanced_prompt = f"基于以下信息：{previous_results}\n执行当前任务..."

    # 执行并更新共享状态
    result = agent.invoke({"messages": [{"role": "user", "content": enhanced_prompt}]})

    # 更新共享状态
    agent_results = previous_results.copy()
    agent_results[state["current_agent"]] = result["messages"][-1].content

    return {
        "messages": result["messages"],
        "agent_results": agent_results
    }
```

### Q3: 如何扩展到更多智能体？

**答：** 使用配置驱动的智能体管理：

```python
class AgentRegistry:
    """智能体注册表"""

    def __init__(self):
        self.agents = {}
        self.capabilities = {}

    def register_agent(self, name: str, agent, capabilities: list):
        """注册智能体"""
        self.agents[name] = agent
        self.capabilities[name] = capabilities

    def find_suitable_agent(self, task: str) -> str:
        """找到合适的智能体"""
        task_lower = task.lower()

        for agent_name, capabilities in self.capabilities.items():
            if any(cap in task_lower for cap in capabilities):
                return agent_name

        return "default_agent"

    def get_agent(self, name: str):
        """获取智能体"""
        return self.agents.get(name)

# 使用注册表
registry = AgentRegistry()
registry.register_agent("research", research_agent, ["搜索", "查找", "信息"])
registry.register_agent("math", math_agent, ["计算", "数学", "数值"])
registry.register_agent("content", content_agent, ["写", "创作", "生成"])
```

## 📖 相关资源

### 官方文档
- [LangGraph 多智能体](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/)
- [智能体协作模式](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)

### 下一步学习
- [15. MCP 集成教学](15_mcp_integration_tutorial.md) - 外部工具集成
- [05. 状态管理教学](05_state_management_tutorial.md) - 复杂状态设计

### 代码示例
- 完整代码：[17_multi_agent_supervisor.py](../../teach_code/17_multi_agent_supervisor.py)
- 运行方式：`python teach_code/17_multi_agent_supervisor.py`

## 🌟 总结

多智能体系统是构建复杂 AI 应用的强大模式：

1. **专业化分工**：每个智能体专注特定领域
2. **中心化协调**：监督者统一管理和调度
3. **灵活扩展**：易于添加新的智能体
4. **容错机制**：单点故障不影响整体系统
5. **协作能力**：智能体间可以共享信息和结果

掌握多智能体系统后，你可以构建企业级的复杂 AI 应用！
