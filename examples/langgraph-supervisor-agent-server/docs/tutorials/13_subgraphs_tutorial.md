# 13. 子图教学

## 🎯 学习目标

通过这个教程，你将学会：
- 子图的概念和设计原理
- 如何创建和组合子图
- 子图间的通信和数据传递
- 模块化架构的最佳实践

## 📚 核心概念

### 1. 什么是子图？

子图是**独立的、可重用的图模块**，可以被其他图调用：

```
主图 → 调用子图A → 子图A执行 → 返回结果 → 主图继续
     → 调用子图B → 子图B执行 → 返回结果 → 主图完成
```

**子图的优势：**
- **模块化**：将复杂逻辑分解为独立模块
- **可重用**：同一子图可被多个主图使用
- **可测试**：独立测试每个子图的功能
- **可维护**：修改子图不影响其他部分

### 2. 子图类型

```python
# 功能子图：执行特定功能
research_subgraph = create_research_subgraph()

# 工作流子图：完整的业务流程
approval_subgraph = create_approval_subgraph()

# 工具子图：封装工具调用
calculation_subgraph = create_calculation_subgraph()
```

### 3. 子图通信

子图通过状态进行通信：

```python
# 输入状态
input_state = {"query": "搜索内容", "max_results": 5}

# 调用子图
result = subgraph.invoke(input_state)

# 输出状态
output_state = {"results": [...], "status": "completed"}
```

## 🔍 代码详细解析

### 基础子图创建

```python
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

# 定义子图状态
class ResearchState(TypedDict):
    query: str
    max_results: int
    results: list
    status: str

def search_web(state: ResearchState):
    """网络搜索节点"""
    query = state["query"]
    max_results = state.get("max_results", 3)

    # 模拟搜索结果
    mock_results = [
        {"title": f"搜索结果1：{query}", "url": "http://example1.com"},
        {"title": f"搜索结果2：{query}", "url": "http://example2.com"},
        {"title": f"搜索结果3：{query}", "url": "http://example3.com"},
    ]

    results = mock_results[:max_results]

    return {
        "results": results,
        "status": "search_completed"
    }

def process_results(state: ResearchState):
    """处理搜索结果"""
    results = state.get("results", [])

    # 简单的结果处理
    processed_results = []
    for i, result in enumerate(results, 1):
        processed_results.append({
            "rank": i,
            "title": result["title"],
            "url": result["url"],
            "summary": f"这是第{i}个搜索结果的摘要"
        })

    return {
        "results": processed_results,
        "status": "processing_completed"
    }

# 创建研究子图
def create_research_subgraph():
    """创建研究子图"""
    builder = StateGraph(ResearchState)

    # 添加节点
    builder.add_node("search", search_web)
    builder.add_node("process", process_results)

    # 添加边
    builder.add_edge(START, "search")
    builder.add_edge("search", "process")
    builder.add_edge("process", END)

    return builder.compile()

# 测试子图
research_subgraph = create_research_subgraph()

def test_research_subgraph():
    """测试研究子图"""
    test_input = {
        "query": "LangGraph教程",
        "max_results": 2
    }

    result = research_subgraph.invoke(test_input)
    print("研究子图结果:")
    print(f"状态: {result['status']}")
    print(f"结果数量: {len(result['results'])}")
    for res in result['results']:
        print(f"  - {res['title']}")
```

### 子图组合

```python
# 定义主图状态
class MainState(TypedDict):
    user_query: str
    research_results: list
    analysis_results: dict
    final_response: str

def prepare_research(state: MainState):
    """准备研究输入"""
    return {
        "query": state["user_query"],
        "max_results": 3
    }

def call_research_subgraph(state: MainState):
    """调用研究子图"""
    # 准备子图输入
    research_input = {
        "query": state["user_query"],
        "max_results": 3,
        "results": [],
        "status": "initialized"
    }

    # 调用子图
    research_result = research_subgraph.invoke(research_input)

    return {
        "research_results": research_result["results"]
    }

def analyze_results(state: MainState):
    """分析研究结果"""
    results = state.get("research_results", [])

    analysis = {
        "total_results": len(results),
        "top_result": results[0] if results else None,
        "summary": f"找到{len(results)}个相关结果"
    }

    return {"analysis_results": analysis}

def generate_final_response(state: MainState):
    """生成最终回复"""
    analysis = state.get("analysis_results", {})
    results = state.get("research_results", [])

    response_parts = [
        f"根据搜索，我找到了{analysis.get('total_results', 0)}个相关结果："
    ]

    for result in results[:2]:  # 显示前2个结果
        response_parts.append(f"- {result['title']}")

    final_response = "\n".join(response_parts)

    return {"final_response": final_response}

# 创建主图
def create_main_graph():
    """创建主图"""
    builder = StateGraph(MainState)

    # 添加节点
    builder.add_node("research", call_research_subgraph)
    builder.add_node("analyze", analyze_results)
    builder.add_node("respond", generate_final_response)

    # 添加边
    builder.add_edge(START, "research")
    builder.add_edge("research", "analyze")
    builder.add_edge("analyze", "respond")
    builder.add_edge("respond", END)

    return builder.compile()

# 测试主图
main_graph = create_main_graph()

def test_main_graph():
    """测试主图"""
    test_input = {
        "user_query": "如何学习Python编程"
    }

    result = main_graph.invoke(test_input)
    print("主图结果:")
    print(result["final_response"])
```

### 条件子图调用

```python
# 定义计算子图状态
class CalculationState(TypedDict):
    expression: str
    result: float
    error: str

def calculate(state: CalculationState):
    """计算节点"""
    expression = state["expression"]

    try:
        # 安全的数学计算
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return {"error": "表达式包含不允许的字符"}

        result = eval(expression)
        return {"result": result, "error": ""}
    except Exception as e:
        return {"error": f"计算错误: {e}"}

# 创建计算子图
def create_calculation_subgraph():
    """创建计算子图"""
    builder = StateGraph(CalculationState)
    builder.add_node("calculate", calculate)
    builder.add_edge(START, "calculate")
    builder.add_edge("calculate", END)
    return builder.compile()

calculation_subgraph = create_calculation_subgraph()

# 智能路由主图
class SmartRouterState(TypedDict):
    user_input: str
    task_type: str
    result: str

def analyze_task(state: SmartRouterState):
    """分析任务类型"""
    user_input = state["user_input"].lower()

    if any(keyword in user_input for keyword in ["计算", "数学", "+", "-", "*", "/"]):
        task_type = "calculation"
    elif any(keyword in user_input for keyword in ["搜索", "查找", "研究"]):
        task_type = "research"
    else:
        task_type = "general"

    return {"task_type": task_type}

def route_to_subgraph(state: SmartRouterState):
    """路由到子图"""
    task_type = state["task_type"]
    user_input = state["user_input"]

    if task_type == "calculation":
        # 提取数学表达式
        import re
        math_match = re.search(r'[\d+\-*/().\s]+', user_input)
        if math_match:
            expression = math_match.group().strip()
            calc_result = calculation_subgraph.invoke({
                "expression": expression,
                "result": 0,
                "error": ""
            })

            if calc_result.get("error"):
                result = f"计算错误: {calc_result['error']}"
            else:
                result = f"计算结果: {expression} = {calc_result['result']}"
        else:
            result = "无法识别数学表达式"

    elif task_type == "research":
        # 提取搜索查询
        query = user_input.replace("搜索", "").replace("查找", "").strip()
        research_result = research_subgraph.invoke({
            "query": query,
            "max_results": 2,
            "results": [],
            "status": "initialized"
        })

        results = research_result.get("results", [])
        if results:
            result = f"搜索结果:\n" + "\n".join([f"- {r['title']}" for r in results])
        else:
            result = "没有找到相关结果"

    else:
        result = "我理解了您的请求，但需要更具体的指令。"

    return {"result": result}

# 创建智能路由图
def create_smart_router():
    """创建智能路由图"""
    builder = StateGraph(SmartRouterState)

    builder.add_node("analyze", analyze_task)
    builder.add_node("route", route_to_subgraph)

    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "route")
    builder.add_edge("route", END)

    return builder.compile()

smart_router = create_smart_router()
```

## 🚀 高级子图模式

### 1. 并行子图执行

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ParallelState(TypedDict):
    query: str
    research_results: list
    calculation_results: dict
    combined_results: dict

async def parallel_subgraph_execution(state: ParallelState):
    """并行执行多个子图"""
    query = state["query"]

    # 准备子图输入
    research_input = {
        "query": query,
        "max_results": 3,
        "results": [],
        "status": "initialized"
    }

    calculation_input = {
        "expression": "2 + 3 * 4",  # 示例计算
        "result": 0,
        "error": ""
    }

    # 并行执行子图
    with ThreadPoolExecutor() as executor:
        research_future = executor.submit(research_subgraph.invoke, research_input)
        calculation_future = executor.submit(calculation_subgraph.invoke, calculation_input)

        # 等待结果
        research_results = research_future.result()
        calculation_results = calculation_future.result()

    # 合并结果
    combined_results = {
        "research_count": len(research_results.get("results", [])),
        "calculation_result": calculation_results.get("result", 0),
        "total_operations": 2
    }

    return {
        "research_results": research_results.get("results", []),
        "calculation_results": calculation_results,
        "combined_results": combined_results
    }

def create_parallel_graph():
    """创建并行执行图"""
    builder = StateGraph(ParallelState)
    builder.add_node("parallel_execute", parallel_subgraph_execution)
    builder.add_edge(START, "parallel_execute")
    builder.add_edge("parallel_execute", END)
    return builder.compile()
```

### 2. 嵌套子图

```python
# 创建数据处理子图
class DataProcessingState(TypedDict):
    raw_data: list
    processed_data: list
    statistics: dict

def clean_data(state: DataProcessingState):
    """清理数据"""
    raw_data = state.get("raw_data", [])

    # 简单的数据清理
    cleaned_data = []
    for item in raw_data:
        if isinstance(item, str) and item.strip():
            cleaned_data.append(item.strip().lower())
        elif isinstance(item, (int, float)):
            cleaned_data.append(item)

    return {"processed_data": cleaned_data}

def calculate_statistics(state: DataProcessingState):
    """计算统计信息"""
    data = state.get("processed_data", [])

    if not data:
        return {"statistics": {}}

    numeric_data = [x for x in data if isinstance(x, (int, float))]

    stats = {
        "total_items": len(data),
        "numeric_items": len(numeric_data),
        "average": sum(numeric_data) / len(numeric_data) if numeric_data else 0,
        "max_value": max(numeric_data) if numeric_data else None,
        "min_value": min(numeric_data) if numeric_data else None
    }

    return {"statistics": stats}

def create_data_processing_subgraph():
    """创建数据处理子图"""
    builder = StateGraph(DataProcessingState)

    builder.add_node("clean", clean_data)
    builder.add_node("stats", calculate_statistics)

    builder.add_edge(START, "clean")
    builder.add_edge("clean", "stats")
    builder.add_edge("stats", END)

    return builder.compile()

data_processing_subgraph = create_data_processing_subgraph()

# 创建包含嵌套子图的主图
class NestedState(TypedDict):
    user_query: str
    search_data: list
    processed_data: list
    final_report: str

def fetch_data(state: NestedState):
    """获取数据（调用研究子图）"""
    query = state["user_query"]

    research_result = research_subgraph.invoke({
        "query": query,
        "max_results": 5,
        "results": [],
        "status": "initialized"
    })

    # 提取数据用于处理
    search_data = [result["title"] for result in research_result.get("results", [])]

    return {"search_data": search_data}

def process_data(state: NestedState):
    """处理数据（调用数据处理子图）"""
    search_data = state.get("search_data", [])

    processing_result = data_processing_subgraph.invoke({
        "raw_data": search_data,
        "processed_data": [],
        "statistics": {}
    })

    return {
        "processed_data": processing_result.get("processed_data", []),
        "statistics": processing_result.get("statistics", {})
    }

def generate_report(state: NestedState):
    """生成报告"""
    stats = state.get("statistics", {})
    processed_data = state.get("processed_data", [])

    report_parts = [
        f"数据处理报告:",
        f"- 总项目数: {stats.get('total_items', 0)}",
        f"- 数值项目数: {stats.get('numeric_items', 0)}",
        f"- 处理后的数据: {len(processed_data)} 项"
    ]

    if processed_data:
        report_parts.append(f"- 示例数据: {processed_data[:3]}")

    final_report = "\n".join(report_parts)

    return {"final_report": final_report}

def create_nested_graph():
    """创建嵌套子图的主图"""
    builder = StateGraph(NestedState)

    builder.add_node("fetch", fetch_data)
    builder.add_node("process", process_data)
    builder.add_node("report", generate_report)

    builder.add_edge(START, "fetch")
    builder.add_edge("fetch", "process")
    builder.add_edge("process", "report")
    builder.add_edge("report", END)

    return builder.compile()
```

### 3. 动态子图选择

```python
class DynamicState(TypedDict):
    task_description: str
    complexity_level: str
    selected_subgraph: str
    result: dict

def analyze_complexity(state: DynamicState):
    """分析任务复杂度"""
    description = state["task_description"].lower()

    # 简单的复杂度分析
    complex_keywords = ["分析", "处理", "统计", "报告"]
    simple_keywords = ["搜索", "查找", "计算"]

    if any(keyword in description for keyword in complex_keywords):
        complexity = "complex"
    elif any(keyword in description for keyword in simple_keywords):
        complexity = "simple"
    else:
        complexity = "medium"

    return {"complexity_level": complexity}

def select_subgraph(state: DynamicState):
    """动态选择子图"""
    complexity = state["complexity_level"]
    description = state["task_description"]

    if complexity == "simple":
        if "计算" in description:
            selected = "calculation"
        else:
            selected = "research"
    elif complexity == "medium":
        selected = "research"
    else:  # complex
        selected = "nested"

    return {"selected_subgraph": selected}

def execute_selected_subgraph(state: DynamicState):
    """执行选定的子图"""
    selected = state["selected_subgraph"]
    description = state["task_description"]

    if selected == "calculation":
        # 提取数学表达式
        import re
        math_match = re.search(r'[\d+\-*/().\s]+', description)
        if math_match:
            expression = math_match.group().strip()
            result = calculation_subgraph.invoke({
                "expression": expression,
                "result": 0,
                "error": ""
            })
        else:
            result = {"error": "无法识别数学表达式"}

    elif selected == "research":
        result = research_subgraph.invoke({
            "query": description,
            "max_results": 3,
            "results": [],
            "status": "initialized"
        })

    elif selected == "nested":
        nested_graph = create_nested_graph()
        result = nested_graph.invoke({
            "user_query": description
        })

    else:
        result = {"error": "未知的子图类型"}

    return {"result": result}

def create_dynamic_graph():
    """创建动态子图选择图"""
    builder = StateGraph(DynamicState)

    builder.add_node("analyze", analyze_complexity)
    builder.add_node("select", select_subgraph)
    builder.add_node("execute", execute_selected_subgraph)

    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "select")
    builder.add_edge("select", "execute")
    builder.add_edge("execute", END)

    return builder.compile()
```

## 🎯 实践练习

### 练习1：工作流子图

```python
# 创建审批工作流子图
class ApprovalState(TypedDict):
    request: str
    requester: str
    amount: float
    approval_level: str
    status: str
    approver: str

def determine_approval_level(state: ApprovalState):
    """确定审批级别"""
    amount = state.get("amount", 0)

    if amount < 1000:
        level = "supervisor"
    elif amount < 10000:
        level = "manager"
    else:
        level = "director"

    return {"approval_level": level}

def process_approval(state: ApprovalState):
    """处理审批"""
    level = state["approval_level"]
    request = state["request"]

    # 模拟审批逻辑
    approvers = {
        "supervisor": "张主管",
        "manager": "李经理",
        "director": "王总监"
    }

    approver = approvers.get(level, "未知")

    # 简单的审批决策
    if "紧急" in request:
        status = "approved"
    elif state.get("amount", 0) > 50000:
        status = "pending_review"
    else:
        status = "approved"

    return {
        "status": status,
        "approver": approver
    }

def create_approval_subgraph():
    """创建审批子图"""
    builder = StateGraph(ApprovalState)

    builder.add_node("determine_level", determine_approval_level)
    builder.add_node("process", process_approval)

    builder.add_edge(START, "determine_level")
    builder.add_edge("determine_level", "process")
    builder.add_edge("process", END)

    return builder.compile()

# 测试审批子图
approval_subgraph = create_approval_subgraph()

def test_approval_workflow():
    """测试审批工作流"""
    test_cases = [
        {"request": "购买办公用品", "requester": "张三", "amount": 500},
        {"request": "紧急设备维修", "requester": "李四", "amount": 5000},
        {"request": "年度培训预算", "requester": "王五", "amount": 80000}
    ]

    for case in test_cases:
        print(f"\n测试案例: {case['request']}")
        result = approval_subgraph.invoke(case)
        print(f"审批级别: {result['approval_level']}")
        print(f"审批人: {result['approver']}")
        print(f"状态: {result['status']}")
```

### 练习2：子图版本管理

```python
class SubgraphRegistry:
    """子图注册表"""

    def __init__(self):
        self.subgraphs = {}
        self.versions = {}

    def register_subgraph(self, name: str, subgraph, version: str = "1.0"):
        """注册子图"""
        if name not in self.subgraphs:
            self.subgraphs[name] = {}
            self.versions[name] = []

        self.subgraphs[name][version] = subgraph
        self.versions[name].append(version)

        print(f"注册子图: {name} v{version}")

    def get_subgraph(self, name: str, version: str = None):
        """获取子图"""
        if name not in self.subgraphs:
            raise ValueError(f"子图 {name} 不存在")

        if version is None:
            # 获取最新版本
            latest_version = max(self.versions[name])
            return self.subgraphs[name][latest_version]

        if version not in self.subgraphs[name]:
            raise ValueError(f"子图 {name} 版本 {version} 不存在")

        return self.subgraphs[name][version]

    def list_subgraphs(self):
        """列出所有子图"""
        for name, versions in self.versions.items():
            print(f"{name}: {', '.join(versions)}")

# 使用示例
registry = SubgraphRegistry()

# 注册不同版本的子图
registry.register_subgraph("research", research_subgraph, "1.0")
registry.register_subgraph("calculation", calculation_subgraph, "1.0")
registry.register_subgraph("approval", approval_subgraph, "1.0")

# 创建改进版本的研究子图
def create_research_subgraph_v2():
    """创建研究子图 v2.0（改进版）"""
    # 这里可以添加更多功能
    return create_research_subgraph()  # 简化示例

registry.register_subgraph("research", create_research_subgraph_v2(), "2.0")

# 列出所有子图
registry.list_subgraphs()

# 使用特定版本的子图
research_v1 = registry.get_subgraph("research", "1.0")
research_latest = registry.get_subgraph("research")  # 获取最新版本
```

### 练习3：子图监控

```python
import time
from functools import wraps

class SubgraphMonitor:
    """子图监控器"""

    def __init__(self):
        self.execution_stats = {}

    def monitor_subgraph(self, name: str):
        """子图监控装饰器"""
        def decorator(subgraph_func):
            @wraps(subgraph_func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = subgraph_func(*args, **kwargs)
                    success = True
                    error = None
                except Exception as e:
                    result = None
                    success = False
                    error = str(e)

                end_time = time.time()
                execution_time = end_time - start_time

                # 记录统计信息
                if name not in self.execution_stats:
                    self.execution_stats[name] = {
                        "total_calls": 0,
                        "successful_calls": 0,
                        "failed_calls": 0,
                        "total_time": 0,
                        "average_time": 0,
                        "last_error": None
                    }

                stats = self.execution_stats[name]
                stats["total_calls"] += 1
                stats["total_time"] += execution_time
                stats["average_time"] = stats["total_time"] / stats["total_calls"]

                if success:
                    stats["successful_calls"] += 1
                else:
                    stats["failed_calls"] += 1
                    stats["last_error"] = error

                print(f"[监控] {name}: {execution_time:.3f}s, 成功: {success}")

                if not success:
                    raise Exception(error)

                return result

            return wrapper
        return decorator

    def get_stats(self, name: str = None):
        """获取统计信息"""
        if name:
            return self.execution_stats.get(name, {})
        return self.execution_stats

    def print_report(self):
        """打印监控报告"""
        print("\n=== 子图监控报告 ===")
        for name, stats in self.execution_stats.items():
            success_rate = (stats["successful_calls"] / stats["total_calls"]) * 100
            print(f"\n{name}:")
            print(f"  总调用次数: {stats['total_calls']}")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  平均执行时间: {stats['average_time']:.3f}s")
            if stats["last_error"]:
                print(f"  最后错误: {stats['last_error']}")

# 使用监控器
monitor = SubgraphMonitor()

@monitor.monitor_subgraph("research")
def monitored_research_call(input_data):
    """被监控的研究子图调用"""
    return research_subgraph.invoke(input_data)

@monitor.monitor_subgraph("calculation")
def monitored_calculation_call(input_data):
    """被监控的计算子图调用"""
    return calculation_subgraph.invoke(input_data)

# 测试监控
def test_monitoring():
    """测试子图监控"""
    # 测试研究子图
    for i in range(3):
        try:
            result = monitored_research_call({
                "query": f"测试查询 {i}",
                "max_results": 2,
                "results": [],
                "status": "initialized"
            })
        except Exception as e:
            print(f"调用失败: {e}")

    # 测试计算子图
    for expr in ["2+3", "5*4", "invalid"]:
        try:
            result = monitored_calculation_call({
                "expression": expr,
                "result": 0,
                "error": ""
            })
        except Exception as e:
            print(f"计算失败: {e}")

    # 打印监控报告
    monitor.print_report()
```

## 🔧 常见问题

### Q1: 子图之间如何共享数据？

**答：** 通过状态传递和共享存储：

```python
# 方法1：通过状态传递
def subgraph_a(state):
    return {"shared_data": "来自子图A的数据"}

def subgraph_b(state):
    shared_data = state.get("shared_data", "")
    return {"result": f"子图B处理了: {shared_data}"}

# 方法2：使用共享存储
from langgraph.store.memory import InMemoryStore

shared_store = InMemoryStore()

def subgraph_with_store(state, *, store):
    store.put(("shared",), "key", "共享数据")
    return state
```

### Q2: 如何处理子图的错误？

**答：** 实现错误处理和回退机制：

```python
def safe_subgraph_call(subgraph, input_data, fallback_result=None):
    """安全的子图调用"""
    try:
        return subgraph.invoke(input_data)
    except Exception as e:
        print(f"子图调用失败: {e}")
        return fallback_result or {"error": str(e)}
```

### Q3: 子图的性能如何优化？

**答：** 使用缓存和并行执行：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_subgraph_call(subgraph_name, input_hash):
    """缓存的子图调用"""
    # 实现缓存逻辑
    pass

# 并行执行多个子图
import asyncio

async def parallel_subgraph_execution(subgraphs, inputs):
    """并行执行多个子图"""
    tasks = []
    for subgraph, input_data in zip(subgraphs, inputs):
        task = asyncio.create_task(
            asyncio.to_thread(subgraph.invoke, input_data)
        )
        tasks.append(task)

    return await asyncio.gather(*tasks)
```

## 📖 相关资源

### 官方文档
- [LangGraph 子图](https://langchain-ai.github.io/langgraph/concepts/low_level/#subgraphs)
- [图组合](https://langchain-ai.github.io/langgraph/concepts/composition/)

### 下一步学习
- [14. 子图内存教学](14_subgraph_memory_tutorial.md) - 子图记忆管理
- [17. 多智能体教学](17_multi_agent_tutorial.md) - 智能体协作

### 代码示例
- 完整代码：[13_subgraphs.py](../../teach_code/13_subgraphs.py)
- 运行方式：`python teach_code/13_subgraphs.py`

## 🌟 总结

子图是构建复杂 LangGraph 应用的关键技术：

1. **模块化设计**：将复杂逻辑分解为独立模块
2. **可重用性**：同一子图可被多个主图使用
3. **可测试性**：独立测试每个子图的功能
4. **可维护性**：修改子图不影响其他部分
5. **灵活组合**：支持嵌套、并行、条件调用

掌握子图后，你可以构建大规模、可维护的 LangGraph 应用！
