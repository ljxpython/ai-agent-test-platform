# 09. 时间旅行教学

## 🎯 学习目标

通过这个教程，你将学会：
- 时间旅行的概念和应用场景
- 如何使用状态历史进行回溯
- 状态分支和修改技术
- 调试和错误恢复的最佳实践

## 📚 核心概念

### 1. 什么是时间旅行？

时间旅行是指**回到图执行的历史状态**，并从该状态继续或修改执行：

```
执行路径: A → B → C → D
时间旅行: 回到 B → 修改 → B' → C' → D'
```

**应用场景：**
- **调试分析**：回到问题发生前的状态
- **错误恢复**：从失败点重新开始
- **A/B 测试**：比较不同执行路径
- **状态探索**：尝试不同的决策分支

### 2. 状态历史

LangGraph 自动保存每个执行步骤的状态：

```python
# 获取状态历史
states = list(graph.get_state_history(config))

for i, historical_state in enumerate(states):
    print(f"步骤 {i + 1}:")
    print(f"  下一个节点: {historical_state.next}")
    print(f"  检查点ID: {historical_state.config['configurable']['checkpoint_id']}")
    print(f"  状态值: {historical_state.values}")
```

### 3. 状态修改和分支

可以修改历史状态并创建新的执行分支：

```python
# 选择历史状态
selected_state = states[1]

# 修改状态
new_config = graph.update_state(
    selected_state.config,
    values={"topic": "新主题"}
)

# 从修改后的状态继续执行
result = graph.invoke(None, new_config)
```

## 🔍 代码详细解析

### 基础时间旅行设置

```python
import uuid
from typing_extensions import TypedDict, NotRequired
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    topic: NotRequired[str]
    joke: NotRequired[str]

def generate_topic(state: State):
    """生成笑话主题"""
    msg = llm.invoke("给我一个有趣的笑话主题")
    return {"topic": msg.content}

def write_joke(state: State):
    """根据主题写笑话"""
    topic = state.get("topic", "通用")
    msg = llm.invoke(f"写一个关于{topic}的简短笑话")
    return {"joke": msg.content}

# 构建工作流
workflow = StateGraph(State)
workflow.add_node("generate_topic", generate_topic)
workflow.add_node("write_joke", write_joke)
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_joke")
workflow.add_edge("write_joke", END)

# 编译（启用检查点以支持时间旅行）
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

### 时间旅行演示

```python
def run_time_travel_demo():
    """运行时间旅行演示"""
    print("时间旅行演示启动！")

    # 创建配置
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # 第一次运行
    print("\n=== 第一次运行 ===")
    state = graph.invoke({}, config)
    print(f"主题: {state.get('topic', '无')}")
    print(f"笑话: {state.get('joke', '无')}")

    # 获取状态历史
    print("\n=== 查看执行历史 ===")
    states = list(graph.get_state_history(config))

    for i, historical_state in enumerate(states):
        print(f"\n步骤 {i + 1}:")
        print(f"  下一个节点: {historical_state.next}")
        print(f"  检查点ID: {historical_state.config['configurable']['checkpoint_id']}")
        print(f"  状态值: {historical_state.values}")

    # 选择一个历史状态进行修改
    if len(states) > 1:
        print(f"\n=== 时间旅行：修改过去的状态 ===")
        selected_state = states[1]  # 选择第二个状态
        print(f"选择的状态: {selected_state.values}")

        # 修改主题
        new_config = graph.update_state(
            selected_state.config,
            values={"topic": "程序员"}
        )
        print(f"修改主题为: 程序员")

        # 从修改后的状态继续执行
        print(f"\n=== 从修改后的状态继续执行 ===")
        final_result = graph.invoke(None, new_config)
        print(f"新的笑话: {final_result.get('joke', '无')}")
```

### 交互式时间旅行

```python
def interactive_time_travel():
    """交互式时间旅行"""
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    while True:
        print("\n选项:")
        print("1. 运行工作流")
        print("2. 查看历史")
        print("3. 时间旅行（修改状态）")
        print("4. 退出")

        choice = input("请选择 (1-4): ").strip()

        if choice == "1":
            print("\n运行工作流...")
            try:
                result = graph.invoke({}, config)
                print(f"结果: {result}")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "2":
            print("\n查看历史...")
            try:
                states = list(graph.get_state_history(config))
                if not states:
                    print("没有历史记录")
                else:
                    for i, state in enumerate(states):
                        print(f"{i}: {state.values} (下一个: {state.next})")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "3":
            print("\n时间旅行...")
            try:
                states = list(graph.get_state_history(config))
                if len(states) < 2:
                    print("需要至少2个历史状态才能进行时间旅行")
                    continue

                print("可用的历史状态:")
                for i, state in enumerate(states):
                    print(f"{i}: {state.values}")

                index = int(input("选择状态索引: "))
                if 0 <= index < len(states):
                    selected_state = states[index]

                    new_topic = input("输入新的主题: ").strip()
                    if new_topic:
                        new_config = graph.update_state(
                            selected_state.config,
                            values={"topic": new_topic}
                        )

                        print("从修改后的状态继续执行...")
                        result = graph.invoke(None, new_config)
                        print(f"新结果: {result}")

                        # 更新配置以使用新的分支
                        config = new_config
                else:
                    print("无效的索引")
            except Exception as e:
                print(f"错误: {e}")

        elif choice == "4":
            print("退出")
            break
        else:
            print("无效选择")
```

## 🚀 高级时间旅行技术

### 1. 状态分支管理

```python
class StateBranchManager:
    """状态分支管理器"""

    def __init__(self, graph):
        self.graph = graph
        self.branches = {}
        self.current_branch = "main"

    def create_branch(self, branch_name: str, from_config: dict):
        """创建新分支"""
        self.branches[branch_name] = {
            "config": from_config,
            "created_at": datetime.datetime.now(),
            "description": f"从检查点创建的分支"
        }
        print(f"创建分支: {branch_name}")

    def switch_branch(self, branch_name: str):
        """切换分支"""
        if branch_name in self.branches:
            self.current_branch = branch_name
            print(f"切换到分支: {branch_name}")
            return self.branches[branch_name]["config"]
        else:
            print(f"分支不存在: {branch_name}")
            return None

    def list_branches(self):
        """列出所有分支"""
        print("可用分支:")
        for name, info in self.branches.items():
            status = "当前" if name == self.current_branch else ""
            print(f"  {name}: {info['description']} {status}")

    def merge_branch(self, source_branch: str, target_branch: str):
        """合并分支（概念性实现）"""
        if source_branch in self.branches and target_branch in self.branches:
            print(f"合并分支: {source_branch} -> {target_branch}")
            # 实际实现需要复杂的状态合并逻辑
        else:
            print("分支不存在，无法合并")

# 使用示例
branch_manager = StateBranchManager(graph)

# 创建主分支
config = {"configurable": {"thread_id": "main_branch"}}
result = graph.invoke({}, config)

# 获取历史状态
states = list(graph.get_state_history(config))
if len(states) > 1:
    # 从历史状态创建分支
    branch_config = graph.update_state(
        states[1].config,
        values={"topic": "科技"}
    )
    branch_manager.create_branch("tech_branch", branch_config)
```

### 2. 调试时间旅行

```python
class DebugTimeTravel:
    """调试时间旅行工具"""

    def __init__(self, graph):
        self.graph = graph
        self.debug_sessions = {}

    def start_debug_session(self, session_name: str, config: dict):
        """开始调试会话"""
        self.debug_sessions[session_name] = {
            "config": config,
            "breakpoints": [],
            "current_step": 0
        }
        print(f"开始调试会话: {session_name}")

    def add_breakpoint(self, session_name: str, step_index: int):
        """添加断点"""
        if session_name in self.debug_sessions:
            self.debug_sessions[session_name]["breakpoints"].append(step_index)
            print(f"在步骤 {step_index} 添加断点")

    def step_through_execution(self, session_name: str):
        """单步执行"""
        if session_name not in self.debug_sessions:
            print("调试会话不存在")
            return

        session = self.debug_sessions[session_name]
        config = session["config"]

        # 获取执行历史
        states = list(self.graph.get_state_history(config))

        print(f"执行历史 ({len(states)} 步):")
        for i, state in enumerate(states):
            is_breakpoint = i in session["breakpoints"]
            marker = "🔴" if is_breakpoint else "⚪"
            print(f"{marker} 步骤 {i}: {state.values}")

            if is_breakpoint:
                print(f"  断点命中！")
                action = input("  操作 (c=继续, i=检查, m=修改, q=退出): ").strip().lower()

                if action == "i":
                    print(f"  状态详情: {state.values}")
                    print(f"  下一个节点: {state.next}")
                elif action == "m":
                    # 允许修改状态
                    new_values = input("  输入新状态值 (JSON格式): ").strip()
                    try:
                        import json
                        modifications = json.loads(new_values)
                        new_config = self.graph.update_state(state.config, values=modifications)
                        print(f"  状态已修改")
                        return new_config
                    except:
                        print("  无效的JSON格式")
                elif action == "q":
                    break

    def compare_executions(self, config1: dict, config2: dict):
        """比较两次执行"""
        states1 = list(self.graph.get_state_history(config1))
        states2 = list(self.graph.get_state_history(config2))

        print("执行比较:")
        max_steps = max(len(states1), len(states2))

        for i in range(max_steps):
            state1 = states1[i] if i < len(states1) else None
            state2 = states2[i] if i < len(states2) else None

            print(f"\n步骤 {i}:")
            if state1:
                print(f"  执行1: {state1.values}")
            if state2:
                print(f"  执行2: {state2.values}")

            if state1 and state2 and state1.values != state2.values:
                print(f"  ⚠️  状态差异detected")

# 使用示例
debug_tool = DebugTimeTravel(graph)

# 开始调试会话
config = {"configurable": {"thread_id": "debug_session"}}
debug_tool.start_debug_session("main_debug", config)

# 运行并添加断点
result = graph.invoke({}, config)
debug_tool.add_breakpoint("main_debug", 1)
debug_tool.step_through_execution("main_debug")
```

### 3. 性能分析时间旅行

```python
import time

class PerformanceTimeTravel:
    """性能分析时间旅行"""

    def __init__(self, graph):
        self.graph = graph
        self.performance_data = {}

    def profile_execution(self, config: dict):
        """性能分析执行"""
        start_time = time.time()

        # 执行图
        result = self.graph.invoke({}, config)

        total_time = time.time() - start_time

        # 获取执行历史
        states = list(self.graph.get_state_history(config))

        # 分析每个步骤的性能
        step_times = []
        for i in range(len(states) - 1):
            # 这里简化处理，实际需要更精确的时间测量
            step_time = total_time / len(states)
            step_times.append(step_time)

        self.performance_data[config["configurable"]["thread_id"]] = {
            "total_time": total_time,
            "step_count": len(states),
            "step_times": step_times,
            "result": result
        }

        return result

    def find_bottlenecks(self, thread_id: str):
        """找出性能瓶颈"""
        if thread_id not in self.performance_data:
            print("没有性能数据")
            return

        data = self.performance_data[thread_id]
        step_times = data["step_times"]

        if not step_times:
            print("没有步骤时间数据")
            return

        # 找出最慢的步骤
        max_time = max(step_times)
        max_index = step_times.index(max_time)

        print(f"性能分析结果:")
        print(f"  总时间: {data['total_time']:.3f}秒")
        print(f"  总步骤: {data['step_count']}")
        print(f"  最慢步骤: 步骤{max_index} ({max_time:.3f}秒)")

        # 建议优化
        if max_time > data['total_time'] * 0.5:
            print(f"  建议: 步骤{max_index}占用了超过50%的时间，需要优化")

    def optimize_execution(self, thread_id: str, target_step: int):
        """优化执行（通过时间旅行）"""
        if thread_id not in self.performance_data:
            print("没有性能数据")
            return

        # 获取原始配置
        config = {"configurable": {"thread_id": thread_id}}
        states = list(self.graph.get_state_history(config))

        if target_step >= len(states):
            print("无效的步骤索引")
            return

        # 从目标步骤重新开始
        target_state = states[target_step]

        print(f"从步骤{target_step}重新开始优化...")

        # 这里可以修改状态或配置来优化性能
        optimized_config = self.graph.update_state(
            target_state.config,
            values=target_state.values  # 可以在这里添加优化
        )

        # 重新执行并测量性能
        start_time = time.time()
        result = self.graph.invoke(None, optimized_config)
        optimized_time = time.time() - start_time

        original_time = self.performance_data[thread_id]["total_time"]
        improvement = ((original_time - optimized_time) / original_time) * 100

        print(f"优化结果:")
        print(f"  原始时间: {original_time:.3f}秒")
        print(f"  优化时间: {optimized_time:.3f}秒")
        print(f"  性能提升: {improvement:.1f}%")

# 使用示例
perf_tool = PerformanceTimeTravel(graph)

# 性能分析
config = {"configurable": {"thread_id": "perf_test"}}
result = perf_tool.profile_execution(config)

# 找出瓶颈
perf_tool.find_bottlenecks("perf_test")

# 尝试优化
perf_tool.optimize_execution("perf_test", 1)
```

## 🎯 实践练习

### 练习1：A/B 测试框架

```python
class ABTestFramework:
    """A/B 测试框架"""

    def __init__(self, graph):
        self.graph = graph
        self.experiments = {}

    def create_experiment(self, experiment_name: str, base_config: dict):
        """创建A/B测试实验"""
        self.experiments[experiment_name] = {
            "base_config": base_config,
            "variants": {},
            "results": {}
        }
        print(f"创建实验: {experiment_name}")

    def add_variant(self, experiment_name: str, variant_name: str, modifications: dict):
        """添加测试变体"""
        if experiment_name not in self.experiments:
            print("实验不存在")
            return

        exp = self.experiments[experiment_name]
        base_config = exp["base_config"]

        # 从基础状态创建变体
        variant_config = self.graph.update_state(base_config, values=modifications)
        exp["variants"][variant_name] = {
            "config": variant_config,
            "modifications": modifications
        }

        print(f"添加变体: {variant_name}")

    def run_experiment(self, experiment_name: str):
        """运行A/B测试"""
        if experiment_name not in self.experiments:
            print("实验不存在")
            return

        exp = self.experiments[experiment_name]

        print(f"运行实验: {experiment_name}")

        # 运行基础版本
        base_result = self.graph.invoke(None, exp["base_config"])
        exp["results"]["base"] = base_result
        print(f"基础版本完成")

        # 运行所有变体
        for variant_name, variant_info in exp["variants"].items():
            variant_result = self.graph.invoke(None, variant_info["config"])
            exp["results"][variant_name] = variant_result
            print(f"变体 {variant_name} 完成")

    def compare_results(self, experiment_name: str):
        """比较实验结果"""
        if experiment_name not in self.experiments:
            print("实验不存在")
            return

        exp = self.experiments[experiment_name]
        results = exp["results"]

        print(f"\n实验结果比较: {experiment_name}")
        print("="*50)

        for version, result in results.items():
            print(f"\n{version}:")
            print(f"  结果: {result}")

            # 可以添加更多的比较指标
            if isinstance(result, dict) and "joke" in result:
                joke_length = len(result["joke"])
                print(f"  笑话长度: {joke_length}")

# 使用示例
ab_test = ABTestFramework(graph)

# 创建实验
base_config = {"configurable": {"thread_id": "ab_test_base"}}
result = graph.invoke({}, base_config)

# 获取基础状态
states = list(graph.get_state_history(base_config))
if states:
    ab_test.create_experiment("joke_experiment", states[0].config)

    # 添加变体
    ab_test.add_variant("joke_experiment", "tech_variant", {"topic": "技术"})
    ab_test.add_variant("joke_experiment", "life_variant", {"topic": "生活"})

    # 运行实验
    ab_test.run_experiment("joke_experiment")

    # 比较结果
    ab_test.compare_results("joke_experiment")
```

### 练习2：错误恢复系统

```python
class ErrorRecoverySystem:
    """错误恢复系统"""

    def __init__(self, graph):
        self.graph = graph
        self.recovery_points = {}
        self.error_log = []

    def create_recovery_point(self, name: str, config: dict):
        """创建恢复点"""
        self.recovery_points[name] = {
            "config": config,
            "timestamp": datetime.datetime.now(),
            "description": f"恢复点: {name}"
        }
        print(f"创建恢复点: {name}")

    def handle_error(self, error: Exception, current_config: dict):
        """处理错误"""
        error_info = {
            "error": str(error),
            "timestamp": datetime.datetime.now(),
            "config": current_config
        }
        self.error_log.append(error_info)

        print(f"错误发生: {error}")
        print("可用的恢复选项:")
        print("1. 从最近的恢复点恢复")
        print("2. 从特定恢复点恢复")
        print("3. 重新开始")

        choice = input("选择恢复方式 (1-3): ").strip()

        if choice == "1":
            return self.recover_from_latest()
        elif choice == "2":
            return self.recover_from_specific()
        elif choice == "3":
            return self.restart_fresh()
        else:
            print("无效选择，从最新恢复点恢复")
            return self.recover_from_latest()

    def recover_from_latest(self):
        """从最新恢复点恢复"""
        if not self.recovery_points:
            print("没有可用的恢复点")
            return None

        latest_point = max(self.recovery_points.items(),
                          key=lambda x: x[1]["timestamp"])

        print(f"从恢复点 {latest_point[0]} 恢复")
        return latest_point[1]["config"]

    def recover_from_specific(self):
        """从特定恢复点恢复"""
        if not self.recovery_points:
            print("没有可用的恢复点")
            return None

        print("可用的恢复点:")
        for name, info in self.recovery_points.items():
            print(f"  {name}: {info['timestamp']}")

        choice = input("选择恢复点: ").strip()

        if choice in self.recovery_points:
            print(f"从恢复点 {choice} 恢复")
            return self.recovery_points[choice]["config"]
        else:
            print("无效的恢复点")
            return None

    def restart_fresh(self):
        """重新开始"""
        print("重新开始执行")
        return {"configurable": {"thread_id": str(uuid.uuid4())}}

    def get_error_report(self):
        """获取错误报告"""
        print("错误报告:")
        for i, error in enumerate(self.error_log, 1):
            print(f"{i}. {error['timestamp']}: {error['error']}")

# 使用示例
recovery_system = ErrorRecoverySystem(graph)

# 创建恢复点
config = {"configurable": {"thread_id": "recovery_test"}}
result = graph.invoke({}, config)
recovery_system.create_recovery_point("after_topic_generation", config)

# 模拟错误处理
try:
    # 这里可能发生错误的代码
    risky_result = graph.invoke({}, config)
except Exception as e:
    recovery_config = recovery_system.handle_error(e, config)
    if recovery_config:
        # 从恢复点继续
        recovered_result = graph.invoke(None, recovery_config)
        print(f"恢复成功: {recovered_result}")
```

## 🔧 常见问题

### Q1: 时间旅行会影响性能吗？

**答：** 会有一定影响，但可以优化：

```python
# 限制历史状态数量
def cleanup_old_states(config: dict, keep_last: int = 10):
    """清理旧状态"""
    states = list(graph.get_state_history(config))
    if len(states) > keep_last:
        # 实际实现需要检查点保存器支持
        print(f"清理 {len(states) - keep_last} 个旧状态")
```

### Q2: 如何处理状态修改的副作用？

**答：** 实现状态验证和一致性检查：

```python
def validate_state_modification(original_state: dict, modified_state: dict) -> bool:
    """验证状态修改的有效性"""
    # 检查必需字段
    required_fields = ["topic"]
    for field in required_fields:
        if field in original_state and field not in modified_state:
            print(f"警告: 缺少必需字段 {field}")
            return False

    # 检查数据类型
    for key, value in modified_state.items():
        if key in original_state:
            if type(value) != type(original_state[key]):
                print(f"警告: 字段 {key} 类型不匹配")
                return False

    return True
```

### Q3: 时间旅行适合生产环境吗？

**答：** 主要用于开发和调试，生产环境需谨慎：

```python
# 生产环境的安全时间旅行
class SafeTimeTravel:
    def __init__(self, graph, enable_in_production: bool = False):
        self.graph = graph
        self.production_mode = not enable_in_production

    def safe_update_state(self, config: dict, values: dict):
        """安全的状态更新"""
        if self.production_mode:
            print("生产环境不允许状态修改")
            return None

        return self.graph.update_state(config, values=values)
```

## 📖 相关资源

### 官方文档
- [LangGraph 状态历史](https://langchain-ai.github.io/langgraph/concepts/persistence/#state-history)
- [状态修改](https://langchain-ai.github.io/langgraph/concepts/persistence/#modifying-state)

### 下一步学习
- [06. 内存检查点教学](06_memory_checkpoint_tutorial.md) - 检查点基础
- [07. SQLite 检查点教学](07_sqlite_checkpoint_tutorial.md) - 持久化存储

### 代码示例
- 完整代码：[09_time_travel.py](../../teach_code/09_time_travel.py)
- 运行方式：`python teach_code/09_time_travel.py`

## 🌟 总结

时间旅行是强大的调试和分析工具：

1. **调试能力**：回到问题发生前的状态
2. **错误恢复**：从失败点重新开始执行
3. **实验分析**：比较不同执行路径的结果
4. **状态探索**：尝试不同的决策和修改
5. **性能优化**：识别和优化性能瓶颈

掌握时间旅行后，你可以更高效地开发和调试 LangGraph 应用！
