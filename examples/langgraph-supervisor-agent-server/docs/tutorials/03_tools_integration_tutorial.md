# 03. 工具集成教学

## 🎯 学习目标

通过这个教程，你将学会：
- 什么是工具集成及其重要性
- 如何在 LangGraph 中集成外部工具
- 工具调用的执行流程
- 处理工具调用的错误和异常

## 📚 核心概念

### 1. 什么是工具集成？

工具集成是指让 AI 智能体能够**调用外部功能**来完成任务，而不仅仅依赖文本生成。例如：

```
用户: "今天北京天气怎么样？"
智能体: 调用天气API → 获取实时数据 → 生成回复
```

**工具的类型：**
- **API 调用**：天气、新闻、股票等
- **数据库操作**：查询、插入、更新
- **文件操作**：读取、写入、处理
- **计算功能**：数学运算、数据分析

### 2. LangGraph 中的工具架构

```
用户输入 → LLM 分析 → 决定调用工具 → 工具执行 → 结果整合 → 最终回复
```

**关键组件：**
- `ToolNode`：工具执行节点
- `tools_condition`：工具调用条件判断
- `bind_tools()`：将工具绑定到 LLM

### 3. 工具调用流程

1. **LLM 分析**：判断是否需要调用工具
2. **工具选择**：选择合适的工具
3. **参数提取**：从用户输入中提取参数
4. **工具执行**：调用工具并获取结果
5. **结果整合**：将工具结果整合到回复中

## 🔍 代码详细解析

### 工具定义和绑定

```python
from langchain_tavily import TavilySearch
from langgraph.prebuilt import ToolNode, tools_condition

# 1. 创建工具实例
tool = TavilySearch(max_results=2)
tools = [tool]

# 2. 绑定工具到 LLM
llm_with_tools = llm.bind_tools(tools)

# 3. 创建工具节点
tool_node = ToolNode(tools=[tool])
```

**解释：**
- `TavilySearch`：第三方搜索工具
- `bind_tools()`：让 LLM 知道可用的工具
- `ToolNode`：专门执行工具调用的节点

### 图结构设计

```python
# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,  # 条件函数
)
graph_builder.add_edge("tools", "chatbot")
```

**图结构：**
```
START → chatbot → tools_condition
                     ↓
                   tools → chatbot → END
                     ↓
                    END
```

### 条件路由逻辑

```python
def tools_condition(state):
    """判断是否需要调用工具"""
    messages = state["messages"]
    last_message = messages[-1]

    # 检查是否有工具调用
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"  # 路由到工具节点
    else:
        return END      # 直接结束
```

### 错误处理和回退

```python
try:
    tool = TavilySearch(max_results=2)
    tools = [tool]
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: State):
        return {"messages": [llm_with_tools.invoke(state["messages"])]}

    # 正常的工具集成图构建...

except Exception as e:
    print(f"工具初始化失败: {e}")

    # 回退到基础聊天机器人
    def chatbot(state: State):
        return {"messages": [llm.invoke(state["messages"])]}

    # 简化的图构建...
```

## 🚀 运行演示

### 基础工具调用

```python
def run_tool_chatbot():
    print("带搜索工具的聊天机器人启动！")
    print("你可以问我任何问题，我会搜索最新信息来回答。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break

        try:
            for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
                for value in event.values():
                    if "messages" in value:
                        message = value["messages"][-1]
                        if hasattr(message, 'content') and message.content:
                            print(f"助手: {message.content}")
                        elif hasattr(message, 'tool_calls') and message.tool_calls:
                            print("正在搜索信息...")
        except Exception as e:
            print(f"处理错误: {e}")
```

### 预期输出

```
用户: 今天的新闻有什么？
正在搜索信息...
助手: 根据最新搜索结果，今天的主要新闻包括：
1. 科技领域：AI技术取得新突破...
2. 经济方面：股市表现稳定...
3. 国际新闻：...

用户: 北京天气怎么样？
正在搜索信息...
助手: 根据最新天气信息，北京今天...
```

## 🔧 高级工具集成

### 1. 多工具协作

```python
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

# 搜索工具
search_tool = TavilySearch(max_results=3)

# 自定义计算工具
@tool
def calculator(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"

# 组合多个工具
tools = [search_tool, calculator]
llm_with_tools = llm.bind_tools(tools)
```

### 2. 工具调用监控

```python
def enhanced_chatbot(state: State):
    """增强的聊天机器人，带工具调用监控"""
    messages = state["messages"]

    # 调用 LLM
    response = llm_with_tools.invoke(messages)

    # 监控工具调用
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"🔧 准备调用 {len(response.tool_calls)} 个工具")
        for tool_call in response.tool_calls:
            print(f"   - {tool_call['name']}: {tool_call['args']}")

    return {"messages": [response]}
```

### 3. 工具结果后处理

```python
class EnhancedToolNode(ToolNode):
    """增强的工具节点，带结果后处理"""

    def __call__(self, state):
        # 调用原始工具节点
        result = super().__call__(state)

        # 后处理工具结果
        if "messages" in result:
            for message in result["messages"]:
                if hasattr(message, 'content'):
                    # 清理和格式化工具输出
                    content = message.content
                    if len(content) > 1000:
                        content = content[:1000] + "..."
                    message.content = f"[工具结果] {content}"

        return result
```

## 🎯 实践练习

### 练习1：创建自定义工具

```python
from langchain_core.tools import tool
import datetime
import random

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def generate_random_number(min_val: int = 1, max_val: int = 100) -> int:
    """生成随机数

    Args:
        min_val: 最小值
        max_val: 最大值
    """
    return random.randint(min_val, max_val)

@tool
def word_count(text: str) -> str:
    """统计文本词数

    Args:
        text: 要统计的文本
    """
    words = text.split()
    chars = len(text)
    return f"词数: {len(words)}, 字符数: {chars}"

# 使用自定义工具
custom_tools = [get_current_time, generate_random_number, word_count]
llm_with_custom_tools = llm.bind_tools(custom_tools)
```

### 练习2：工具调用统计

```python
class ToolUsageTracker:
    """工具使用统计器"""

    def __init__(self):
        self.usage_stats = {}

    def track_tool_call(self, tool_name: str):
        """记录工具调用"""
        if tool_name not in self.usage_stats:
            self.usage_stats[tool_name] = 0
        self.usage_stats[tool_name] += 1

    def get_stats(self):
        """获取统计信息"""
        total_calls = sum(self.usage_stats.values())
        return {
            "total_calls": total_calls,
            "tool_usage": self.usage_stats,
            "most_used": max(self.usage_stats.items(), key=lambda x: x[1]) if self.usage_stats else None
        }

# 集成到工具节点
tracker = ToolUsageTracker()

def tracked_chatbot(state: State):
    """带统计的聊天机器人"""
    response = llm_with_tools.invoke(state["messages"])

    # 统计工具调用
    if hasattr(response, 'tool_calls') and response.tool_calls:
        for tool_call in response.tool_calls:
            tracker.track_tool_call(tool_call['name'])

    return {"messages": [response]}
```

### 练习3：条件工具调用

```python
def smart_tool_selection(state: State):
    """智能工具选择"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {"messages": [llm.invoke(messages)]}

    user_content = last_message.content.lower()

    # 根据内容选择不同的工具集
    if any(keyword in user_content for keyword in ["搜索", "查找", "新闻"]):
        # 使用搜索工具
        tools = [search_tool]
    elif any(keyword in user_content for keyword in ["计算", "数学"]):
        # 使用计算工具
        tools = [calculator]
    elif any(keyword in user_content for keyword in ["时间", "日期"]):
        # 使用时间工具
        tools = [get_current_time]
    else:
        # 不使用工具
        tools = []

    if tools:
        llm_with_selected_tools = llm.bind_tools(tools)
        response = llm_with_selected_tools.invoke(messages)
    else:
        response = llm.invoke(messages)

    return {"messages": [response]}
```

## 🔧 常见问题

### Q1: 工具调用失败怎么办？

**答：** 实现工具调用的错误处理：

```python
def robust_tool_node(state):
    """健壮的工具节点"""
    try:
        return tool_node(state)
    except Exception as e:
        error_message = f"工具调用失败: {e}"
        return {
            "messages": [{
                "role": "assistant",
                "content": error_message
            }]
        }
```

### Q2: 如何限制工具调用的权限？

**答：** 实现工具调用的权限检查：

```python
def secure_tool_call(tool_name: str, args: dict) -> bool:
    """检查工具调用权限"""
    # 危险操作列表
    dangerous_operations = ["delete", "remove", "drop"]

    # 检查工具名称
    if any(op in tool_name.lower() for op in dangerous_operations):
        return False

    # 检查参数
    for value in args.values():
        if isinstance(value, str) and any(op in value.lower() for op in dangerous_operations):
            return False

    return True
```

### Q3: 工具调用太慢怎么优化？

**答：** 实现异步工具调用和缓存：

```python
import asyncio
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str):
    """带缓存的搜索"""
    return search_tool.invoke(query)

async def async_tool_call(tool, args):
    """异步工具调用"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, tool.invoke, args)
```

### Q4: 如何处理工具返回的大量数据？

**答：** 实现结果摘要和分页：

```python
def summarize_tool_result(result: str, max_length: int = 500) -> str:
    """摘要工具结果"""
    if len(result) <= max_length:
        return result

    # 简单截断
    truncated = result[:max_length-3] + "..."

    # 或者使用 LLM 生成摘要
    summary_prompt = f"请总结以下内容：\n{result}"
    summary = llm.invoke([{"role": "user", "content": summary_prompt}])

    return summary.content
```

## 📖 相关资源

### 官方文档
- [LangGraph 工具使用](https://langchain-ai.github.io/langgraph/concepts/tool_calling/)
- [LangChain 工具集成](https://python.langchain.com/docs/modules/tools/)

### 常用工具
- [Tavily Search](https://tavily.com/) - 网络搜索
- [LangChain Tools](https://python.langchain.com/docs/integrations/tools/) - 工具集合

### 下一步学习
- [04. 自定义工具教学](04_custom_tools_tutorial.md) - 创建自定义工具
- [08. 人机交互教学](08_human_in_loop_tutorial.md) - 人工干预工具

### 代码示例
- 完整代码：[03_chatbot_with_tools.py](../../teach_code/03_chatbot_with_tools.py)
- 运行方式：`python teach_code/03_chatbot_with_tools.py`

## 🌟 总结

工具集成是 LangGraph 的核心功能之一：

1. **扩展能力**：让 AI 能够执行实际操作
2. **实时数据**：获取最新信息而非训练数据
3. **条件路由**：智能判断何时使用工具
4. **错误处理**：robust 的异常处理机制
5. **性能优化**：缓存、异步、结果处理

掌握工具集成后，你的 LangGraph 应用将具备真正的实用价值！
