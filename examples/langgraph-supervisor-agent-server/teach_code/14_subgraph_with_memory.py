import operator
from typing import Annotated

from config import llm
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class MainState(TypedDict):
    user_input: str
    subgraph_results: Annotated[list, operator.add]
    final_summary: str


class SubgraphState(TypedDict):
    task: str
    step_count: Annotated[int, operator.add]
    results: Annotated[list, operator.add]


def create_worker_subgraph():
    """创建带独立内存的工作子图"""

    def initialize_task(state: SubgraphState):
        """初始化任务"""
        task = state["task"]
        return {"step_count": 1, "results": [f"开始处理任务: {task}"]}

    def process_step(state: SubgraphState):
        """处理步骤"""
        task = state["task"]
        current_step = state.get("step_count", 0)

        # 模拟处理步骤
        step_result = f"步骤 {current_step}: 处理 '{task}' 中..."

        return {"step_count": 1, "results": [step_result]}

    def finalize_task(state: SubgraphState):
        """完成任务"""
        task = state["task"]
        total_steps = state.get("step_count", 0)

        final_result = f"任务 '{task}' 完成，共 {total_steps} 步"

        return {"results": [final_result]}

    # 构建子图（带独立检查点）
    subgraph_builder = StateGraph(SubgraphState)
    subgraph_builder.add_node("initialize", initialize_task)
    subgraph_builder.add_node("process", process_step)
    subgraph_builder.add_node("finalize", finalize_task)

    subgraph_builder.add_edge(START, "initialize")
    subgraph_builder.add_edge("initialize", "process")
    subgraph_builder.add_edge("process", "finalize")
    subgraph_builder.add_edge("finalize", END)

    # 编译子图（带独立内存）
    return subgraph_builder.compile(checkpointer=InMemorySaver())


# 创建子图实例
worker_subgraph = create_worker_subgraph()


def delegate_to_subgraph(state: MainState):
    """委托给子图处理"""
    user_input = state["user_input"]

    # 分解任务
    tasks = user_input.split("，")  # 简单的任务分解

    results = []
    for i, task in enumerate(tasks):
        # 为每个任务创建独立的配置
        config = {"configurable": {"thread_id": f"task_{i}"}}

        # 调用子图
        subgraph_result = worker_subgraph.invoke({"task": task.strip()}, config)

        results.append(
            {
                "task": task.strip(),
                "results": subgraph_result["results"],
                "steps": subgraph_result["step_count"],
            }
        )

    return {"subgraph_results": results}


def summarize_results(state: MainState):
    """汇总结果"""
    results = state["subgraph_results"]

    summary_lines = ["=== 任务执行汇总 ==="]
    total_steps = 0

    for result in results:
        task = result["task"]
        steps = result["steps"]
        total_steps += steps

        summary_lines.append(f"任务: {task}")
        summary_lines.append(f"  步骤数: {steps}")
        summary_lines.append(f"  结果: {result['results'][-1]}")  # 最后一个结果
        summary_lines.append("")

    summary_lines.append(f"总计步骤数: {total_steps}")

    return {"final_summary": "\n".join(summary_lines)}


# 构建主图
main_checkpointer = InMemorySaver()

main_graph_builder = StateGraph(MainState)
main_graph_builder.add_node("delegate", delegate_to_subgraph)
main_graph_builder.add_node("summarize", summarize_results)

main_graph_builder.add_edge(START, "delegate")
main_graph_builder.add_edge("delegate", "summarize")
main_graph_builder.add_edge("summarize", END)

# 编译主图（带主图内存）
main_graph = main_graph_builder.compile(checkpointer=main_checkpointer)


def run_subgraph_memory_demo():
    """运行带独立内存的子图演示"""
    print("带独立内存的子图演示启动！")
    print("这个演示展示子图如何拥有独立的内存状态。")
    print("输入多个任务（用逗号分隔），每个任务会在独立的子图中处理。")
    print("输入 'quit' 退出，输入 'history' 查看历史。")

    # 主图配置
    main_config = {"configurable": {"thread_id": "main_session"}}

    while True:
        user_input = input("\n请输入任务（用逗号分隔）: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if user_input.lower() == "history":
            try:
                # 查看主图历史
                main_state = main_graph.get_state(main_config)
                if main_state.values:
                    print("\n=== 主图历史 ===")
                    print(
                        f"最后处理的输入: {main_state.values.get('user_input', '无')}"
                    )
                    if main_state.values.get("final_summary"):
                        print(main_state.values["final_summary"])
                else:
                    print("没有历史记录")
            except Exception as e:
                print(f"获取历史失败: {e}")
            continue

        try:
            # 运行主图
            result = main_graph.invoke({"user_input": user_input}, main_config)

            print(result["final_summary"])

        except Exception as e:
            print(f"处理错误: {e}")


def inspect_subgraph_memory():
    """检查子图内存"""
    print("\n" + "=" * 50)
    print("子图内存检查")
    print("=" * 50)

    # 模拟一些任务来创建子图状态
    test_tasks = ["任务A", "任务B", "任务C"]

    print("创建测试子图状态...")
    for i, task in enumerate(test_tasks):
        config = {"configurable": {"thread_id": f"task_{i}"}}
        try:
            result = worker_subgraph.invoke({"task": task}, config)
            print(f"任务 {i}: {task} - 完成")
        except Exception as e:
            print(f"任务 {i} 失败: {e}")

    print("\n检查子图状态...")
    for i in range(len(test_tasks)):
        config = {"configurable": {"thread_id": f"task_{i}"}}
        try:
            state = worker_subgraph.get_state(config)
            if state.values:
                print(f"\n子图 {i} 状态:")
                print(f"  任务: {state.values.get('task', '未知')}")
                print(f"  步骤数: {state.values.get('step_count', 0)}")
                print(f"  结果数: {len(state.values.get('results', []))}")
        except Exception as e:
            print(f"获取子图 {i} 状态失败: {e}")


def demo_memory_isolation():
    """演示内存隔离"""
    print("\n" + "=" * 50)
    print("内存隔离演示")
    print("=" * 50)

    # 创建多个独立的子图实例
    subgraph1 = create_worker_subgraph()
    subgraph2 = create_worker_subgraph()

    config1 = {"configurable": {"thread_id": "isolated_1"}}
    config2 = {"configurable": {"thread_id": "isolated_2"}}

    print("=== 子图1处理任务 ===")
    result1 = subgraph1.invoke({"task": "数据处理"}, config1)
    print(f"子图1结果: {result1}")

    print("\n=== 子图2处理任务 ===")
    result2 = subgraph2.invoke({"task": "文件分析"}, config2)
    print(f"子图2结果: {result2}")

    # 检查状态隔离
    print("\n=== 检查状态隔离 ===")
    state1 = subgraph1.get_state(config1)
    state2 = subgraph2.get_state(config2)

    print(f"子图1状态: {state1.values}")
    print(f"子图2状态: {state2.values}")
    print("✅ 状态完全隔离")


def demo_persistent_subgraph_memory():
    """演示子图内存持久化"""
    print("\n" + "=" * 50)
    print("子图内存持久化演示")
    print("=" * 50)

    # 创建一个持久化的子图配置
    persistent_config = {"configurable": {"thread_id": "persistent_task"}}

    # 第一次调用
    print("=== 第一次调用子图 ===")
    result1 = worker_subgraph.invoke({"task": "长期项目"}, persistent_config)
    print(f"第一次结果: {result1}")

    # 获取状态
    state_after_first = worker_subgraph.get_state(persistent_config)
    print(f"第一次后状态: {state_after_first.values}")

    # 模拟"重启"后的第二次调用
    print("\n=== 模拟重启后的第二次调用 ===")

    # 创建新的子图实例（模拟重启）
    new_worker_subgraph = create_worker_subgraph()

    # 使用相同的配置，应该能恢复状态
    try:
        # 注意：这里我们不能直接恢复状态，因为是新实例
        # 但在真实场景中，使用相同的检查点保存器可以实现状态恢复
        result2 = new_worker_subgraph.invoke({"task": "继续项目"}, persistent_config)
        print(f"第二次结果: {result2}")

        state_after_second = new_worker_subgraph.get_state(persistent_config)
        print(f"第二次后状态: {state_after_second.values}")

    except Exception as e:
        print(f"状态恢复演示: {e}")
        print("注意：在实际应用中，使用共享的检查点保存器可以实现真正的状态持久化")


def demo_complex_subgraph_workflow():
    """演示复杂子图工作流"""
    print("\n" + "=" * 50)
    print("复杂子图工作流演示")
    print("=" * 50)

    # 创建一个更复杂的子图，包含条件分支
    class ComplexSubgraphState(TypedDict):
        task_type: str
        task_data: str
        processing_path: str
        result: str

    def classify_task(state: ComplexSubgraphState):
        """任务分类"""
        task_data = state["task_data"]

        if "计算" in task_data or "数学" in task_data:
            path = "math"
        elif "文本" in task_data or "分析" in task_data:
            path = "text"
        else:
            path = "general"

        return {"processing_path": path}

    def process_math_task(state: ComplexSubgraphState):
        """处理数学任务"""
        return {"result": f"数学处理完成: {state['task_data']}"}

    def process_text_task(state: ComplexSubgraphState):
        """处理文本任务"""
        return {"result": f"文本处理完成: {state['task_data']}"}

    def process_general_task(state: ComplexSubgraphState):
        """处理一般任务"""
        return {"result": f"一般处理完成: {state['task_data']}"}

    def route_by_path(state: ComplexSubgraphState):
        """根据路径路由"""
        return state["processing_path"]

    # 构建复杂子图
    complex_subgraph = StateGraph(ComplexSubgraphState)
    complex_subgraph.add_node("classify", classify_task)
    complex_subgraph.add_node("math", process_math_task)
    complex_subgraph.add_node("text", process_text_task)
    complex_subgraph.add_node("general", process_general_task)

    complex_subgraph.add_edge(START, "classify")
    complex_subgraph.add_conditional_edges(
        "classify",
        route_by_path,
        {"math": "math", "text": "text", "general": "general"},
    )
    complex_subgraph.add_edge("math", END)
    complex_subgraph.add_edge("text", END)
    complex_subgraph.add_edge("general", END)

    compiled_complex = complex_subgraph.compile(checkpointer=InMemorySaver())

    # 测试复杂子图
    test_cases = [
        {"task_type": "A", "task_data": "计算平均值"},
        {"task_type": "B", "task_data": "文本情感分析"},
        {"task_type": "C", "task_data": "图像处理"},
    ]

    for i, test_case in enumerate(test_cases):
        config = {"configurable": {"thread_id": f"complex_{i}"}}
        print(f"\n测试案例 {i+1}: {test_case['task_data']}")

        result = compiled_complex.invoke(test_case, config)
        print(f"处理路径: {result['processing_path']}")
        print(f"处理结果: {result['result']}")


if __name__ == "__main__":
    run_subgraph_memory_demo()
    inspect_subgraph_memory()
    demo_memory_isolation()
    demo_persistent_subgraph_memory()
    demo_complex_subgraph_workflow()
