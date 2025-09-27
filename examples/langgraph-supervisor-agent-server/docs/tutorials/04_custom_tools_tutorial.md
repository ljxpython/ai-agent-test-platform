# 04. 自定义工具教学

## 🎯 学习目标

通过这个教程，你将学会：
- 如何创建自定义工具
- 工具参数定义和类型检查
- 工具的错误处理和验证
- 工具的最佳实践和设计模式

## 📚 核心概念

### 1. 什么是自定义工具？

自定义工具是你为特定需求创建的功能模块，让 AI 智能体能够执行特定的操作：

```python
@tool
def my_custom_tool(param: str) -> str:
    """工具描述"""
    # 工具逻辑
    return result
```

**自定义工具的优势：**
- **针对性强**：专门解决特定问题
- **可控性高**：完全掌控执行逻辑
- **集成简单**：与现有系统无缝集成
- **扩展性好**：可以随时修改和优化

### 2. 工具装饰器 @tool

`@tool` 装饰器是创建工具的核心：

```python
from langchain_core.tools import tool

@tool
def calculate(expression: str) -> str:
    """计算数学表达式

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"

    Returns:
        计算结果字符串
    """
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"
```

**关键要素：**
- **函数名**：工具的标识符
- **文档字符串**：工具的描述（AI 会看到）
- **类型注解**：参数和返回值类型
- **参数文档**：Args 部分描述参数用途

### 3. 工具参数类型

支持多种参数类型：

```python
@tool
def multi_param_tool(
    text: str,           # 字符串
    number: int,         # 整数
    decimal: float,      # 浮点数
    flag: bool,          # 布尔值
    items: list,         # 列表
    data: dict           # 字典
) -> str:
    """多参数类型示例"""
    return f"处理完成: {text}, {number}, {decimal}, {flag}, {items}, {data}"
```

## 🔍 代码详细解析

### 基础工具创建

```python
import datetime
import random
from langchain_core.tools import tool

@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def generate_random_number(min_val: int = 1, max_val: int = 100) -> int:
    """生成指定范围内的随机数

    Args:
        min_val: 最小值
        max_val: 最大值
    """
    return random.randint(min_val, max_val)
```

**解释：**
- `get_current_time`：无参数工具
- `generate_random_number`：带默认值的参数
- 返回类型明确指定

### 复杂工具实现

```python
@tool
def calculate(expression: str) -> str:
    """计算数学表达式

    Args:
        expression: 数学表达式，如 "2 + 3 * 4"
    """
    try:
        # 安全的数学计算
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"
```

**安全考虑：**
- 输入验证：检查允许的字符
- 异常处理：捕获计算错误
- 错误信息：提供有用的错误反馈

### 工具集成到图中

```python
# 设置工具
tools = [get_current_time, generate_random_number, calculate]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    """带自定义工具的聊天机器人"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# 添加工具节点
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# 添加条件边
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
```

## 🚀 运行演示

### 基础工具测试

```python
def test_custom_tools():
    """测试自定义工具"""
    print("测试自定义工具:")

    # 测试时间工具
    current_time = get_current_time.invoke({})
    print(f"当前时间: {current_time}")

    # 测试随机数工具
    random_num = generate_random_number.invoke({"min_val": 1, "max_val": 10})
    print(f"随机数: {random_num}")

    # 测试计算工具
    calc_result = calculate.invoke({"expression": "2 + 3 * 4"})
    print(f"计算结果: {calc_result}")
```

### 预期输出

```
用户: 现在几点了？
助手: 当前时间是 2024-01-15 14:30:25

用户: 给我一个1到100的随机数
助手: 我为你生成了一个随机数：42

用户: 计算 (5 + 3) * 2
助手: 计算结果：(5 + 3) * 2 = 16
```

## 🎯 高级工具设计

### 1. 带状态的工具

```python
class StatefulTool:
    """带状态的工具类"""

    def __init__(self):
        self.call_count = 0
        self.history = []

    @tool
    def count_calls(self, message: str) -> str:
        """统计工具调用次数"""
        self.call_count += 1
        self.history.append(message)
        return f"这是第 {self.call_count} 次调用，消息：{message}"

# 使用
stateful_tool = StatefulTool()
tools.append(stateful_tool.count_calls)
```

### 2. 异步工具

```python
import asyncio
from langchain_core.tools import tool

@tool
async def async_web_request(url: str) -> str:
    """异步网络请求工具"""
    try:
        # 模拟异步请求
        await asyncio.sleep(1)
        return f"已获取 {url} 的内容"
    except Exception as e:
        return f"请求失败: {e}"

# 在异步环境中使用
async def async_tool_demo():
    result = await async_web_request.ainvoke({"url": "https://example.com"})
    print(result)
```

### 3. 工具链组合

```python
@tool
def preprocess_text(text: str) -> str:
    """文本预处理"""
    return text.strip().lower()

@tool
def analyze_text(text: str) -> str:
    """文本分析"""
    word_count = len(text.split())
    char_count = len(text)
    return f"词数: {word_count}, 字符数: {char_count}"

@tool
def text_pipeline(text: str) -> str:
    """文本处理管道"""
    # 组合多个工具
    processed = preprocess_text.invoke({"text": text})
    analysis = analyze_text.invoke({"text": processed})
    return f"处理结果: {processed}\n分析结果: {analysis}"
```

## 🎯 实践练习

### 练习1：文件操作工具

```python
import os
from pathlib import Path

@tool
def read_file(filename: str) -> str:
    """读取文件内容

    Args:
        filename: 文件名
    """
    try:
        # 安全检查
        if not filename.endswith(('.txt', '.md', '.py')):
            return "错误：只支持 .txt, .md, .py 文件"

        # 防止路径遍历攻击
        safe_path = Path(filename).resolve()
        if not str(safe_path).startswith(str(Path.cwd())):
            return "错误：不允许访问当前目录外的文件"

        with open(safe_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return f"文件内容:\n{content}"
    except FileNotFoundError:
        return f"错误：文件 {filename} 不存在"
    except Exception as e:
        return f"读取错误: {e}"

@tool
def write_file(filename: str, content: str) -> str:
    """写入文件

    Args:
        filename: 文件名
        content: 文件内容
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"已写入文件: {filename}"
    except Exception as e:
        return f"写入错误: {e}"
```

### 练习2：数据处理工具

```python
import json
import csv
from io import StringIO

@tool
def parse_json(json_str: str) -> str:
    """解析 JSON 字符串"""
    try:
        data = json.loads(json_str)
        return f"JSON 解析成功，包含 {len(data)} 个项目"
    except json.JSONDecodeError as e:
        return f"JSON 解析错误: {e}"

@tool
def parse_csv(csv_str: str) -> str:
    """解析 CSV 字符串"""
    try:
        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)
        return f"CSV 解析成功，包含 {len(rows)} 行数据"
    except Exception as e:
        return f"CSV 解析错误: {e}"

@tool
def calculate_statistics(numbers: str) -> str:
    """计算数字统计信息

    Args:
        numbers: 逗号分隔的数字字符串，如 "1,2,3,4,5"
    """
    try:
        nums = [float(x.strip()) for x in numbers.split(',')]

        if not nums:
            return "错误：没有提供数字"

        mean = sum(nums) / len(nums)
        max_val = max(nums)
        min_val = min(nums)

        return f"""统计结果:
平均值: {mean:.2f}
最大值: {max_val}
最小值: {min_val}
总数: {len(nums)}"""
    except ValueError:
        return "错误：请提供有效的数字"
    except Exception as e:
        return f"计算错误: {e}"
```

### 练习3：系统信息工具

```python
import platform
import psutil
import os

@tool
def get_system_info() -> str:
    """获取系统信息"""
    try:
        info = {
            "操作系统": platform.system(),
            "版本": platform.version(),
            "架构": platform.machine(),
            "处理器": platform.processor(),
            "Python版本": platform.python_version()
        }

        return "\n".join([f"{k}: {v}" for k, v in info.items()])
    except Exception as e:
        return f"获取系统信息失败: {e}"

@tool
def get_memory_usage() -> str:
    """获取内存使用情况"""
    try:
        memory = psutil.virtual_memory()
        return f"""内存使用情况:
总内存: {memory.total / (1024**3):.2f} GB
已使用: {memory.used / (1024**3):.2f} GB
可用: {memory.available / (1024**3):.2f} GB
使用率: {memory.percent}%"""
    except Exception as e:
        return f"获取内存信息失败: {e}"
```

## 🔧 工具设计最佳实践

### 1. 输入验证

```python
@tool
def safe_calculator(expression: str) -> str:
    """安全的计算器"""
    # 1. 长度检查
    if len(expression) > 100:
        return "错误：表达式太长"

    # 2. 字符检查
    allowed_chars = set('0123456789+-*/().')
    if not all(c in allowed_chars or c.isspace() for c in expression):
        return "错误：包含不允许的字符"

    # 3. 括号匹配检查
    if expression.count('(') != expression.count(')'):
        return "错误：括号不匹配"

    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"
```

### 2. 错误处理模式

```python
@tool
def robust_tool(data: str) -> str:
    """健壮的工具示例"""
    try:
        # 主要逻辑
        result = process_data(data)
        return f"处理成功: {result}"

    except ValueError as e:
        # 特定错误处理
        return f"数据格式错误: {e}"

    except FileNotFoundError as e:
        # 文件错误处理
        return f"文件不存在: {e}"

    except Exception as e:
        # 通用错误处理
        return f"处理失败: {e}"
```

### 3. 工具文档规范

```python
@tool
def well_documented_tool(
    required_param: str,
    optional_param: int = 10,
    flag: bool = False
) -> str:
    """工具的详细描述

    这个工具用于演示良好的文档规范。

    Args:
        required_param: 必需参数的描述
        optional_param: 可选参数的描述，默认值为 10
        flag: 布尔标志，默认为 False

    Returns:
        处理结果的字符串描述

    Examples:
        >>> well_documented_tool("test")
        "处理完成: test"

    Raises:
        ValueError: 当参数无效时
    """
    if not required_param:
        raise ValueError("required_param 不能为空")

    return f"处理完成: {required_param}, {optional_param}, {flag}"
```

## 🔧 常见问题

### Q1: 工具参数类型不匹配怎么办？

**答：** 使用 Pydantic 模型进行严格类型检查：

```python
from pydantic import BaseModel, Field

class CalculatorInput(BaseModel):
    expression: str = Field(description="数学表达式")
    precision: int = Field(default=2, description="小数精度")

@tool(args_schema=CalculatorInput)
def typed_calculator(expression: str, precision: int = 2) -> str:
    """类型安全的计算器"""
    result = eval(expression)
    return f"{expression} = {result:.{precision}f}"
```

### Q2: 如何处理工具的副作用？

**答：** 实现事务性操作和回滚机制：

```python
@tool
def transactional_operation(data: str) -> str:
    """事务性操作"""
    backup = create_backup()

    try:
        # 执行操作
        result = perform_operation(data)
        commit_changes()
        return f"操作成功: {result}"

    except Exception as e:
        # 回滚操作
        restore_backup(backup)
        return f"操作失败，已回滚: {e}"
```

### Q3: 工具执行时间太长怎么办？

**答：** 实现超时和进度监控：

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError("操作超时")

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

@tool
def long_running_tool(data: str) -> str:
    """长时间运行的工具"""
    try:
        with timeout(30):  # 30秒超时
            result = expensive_operation(data)
            return f"操作完成: {result}"
    except TimeoutError:
        return "操作超时，请稍后重试"
```

## 📖 相关资源

### 官方文档
- [LangChain 自定义工具](https://python.langchain.com/docs/modules/tools/custom_tools/)
- [工具最佳实践](https://python.langchain.com/docs/modules/tools/)

### 下一步学习
- [05. 状态管理教学](05_state_management_tutorial.md) - 复杂状态设计
- [08. 人机交互教学](08_human_in_loop_tutorial.md) - 工具审批流程

### 代码示例
- 完整代码：[04_custom_tools.py](../../teach_code/04_custom_tools.py)
- 运行方式：`python teach_code/04_custom_tools.py`

## 🌟 总结

自定义工具是 LangGraph 应用的核心扩展机制：

1. **灵活性**：完全自定义的功能实现
2. **类型安全**：严格的参数类型检查
3. **错误处理**：robust 的异常处理机制
4. **文档规范**：清晰的工具描述和参数说明
5. **最佳实践**：安全、高效、可维护的设计

掌握自定义工具后，你可以为 LangGraph 应用添加任何所需的功能！
