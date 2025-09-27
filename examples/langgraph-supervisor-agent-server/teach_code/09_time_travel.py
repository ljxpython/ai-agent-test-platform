import uuid

from config import llm
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import NotRequired, TypedDict


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

# 添加边
workflow.add_edge(START, "generate_topic")
workflow.add_edge("generate_topic", "write_joke")
workflow.add_edge("write_joke", END)

# 编译（启用检查点以支持时间旅行）
checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)


def run_time_travel_demo():
    """运行时间旅行演示"""
    print("时间旅行演示启动！")
    print("这个演示会生成笑话，然后展示如何回到过去的状态。")

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
        selected_state = states[1]  # 选择第二个状态（生成主题后）
        print(f"选择的状态: {selected_state.values}")

        # 修改主题
        new_config = graph.update_state(
            selected_state.config, values={"topic": "程序员"}
        )
        print(f"修改主题为: 程序员")
        print(f"新的检查点ID: {new_config['configurable']['checkpoint_id']}")

        # 从修改后的状态继续执行
        print(f"\n=== 从修改后的状态继续执行 ===")
        final_result = graph.invoke(None, new_config)
        print(f"新的笑话: {final_result.get('joke', '无')}")

        # 显示新的历史
        print(f"\n=== 新的执行历史 ===")
        new_states = list(graph.get_state_history(new_config))
        for i, state in enumerate(new_states):
            print(f"步骤 {i + 1}: {state.values}")


def interactive_time_travel():
    """交互式时间旅行"""
    print("\n" + "=" * 50)
    print("交互式时间旅行演示")
    print("=" * 50)

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
                            selected_state.config, values={"topic": new_topic}
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


def advanced_time_travel_demo():
    """高级时间旅行演示"""
    print("\n" + "=" * 50)
    print("高级时间旅行演示")
    print("=" * 50)

    # 创建一个更复杂的工作流
    class AdvancedState(TypedDict):
        step: NotRequired[int]
        data: NotRequired[str]
        processed: NotRequired[bool]

    def step1(state: AdvancedState):
        return {"step": 1, "data": "初始数据"}

    def step2(state: AdvancedState):
        data = state.get("data", "")
        return {"step": 2, "data": f"{data} -> 处理中"}

    def step3(state: AdvancedState):
        data = state.get("data", "")
        return {"step": 3, "data": f"{data} -> 完成", "processed": True}

    # 构建高级工作流
    advanced_workflow = StateGraph(AdvancedState)
    advanced_workflow.add_node("step1", step1)
    advanced_workflow.add_node("step2", step2)
    advanced_workflow.add_node("step3", step3)

    advanced_workflow.add_edge(START, "step1")
    advanced_workflow.add_edge("step1", "step2")
    advanced_workflow.add_edge("step2", "step3")
    advanced_workflow.add_edge("step3", END)

    advanced_graph = advanced_workflow.compile(checkpointer=InMemorySaver())

    config = {"configurable": {"thread_id": "advanced_demo"}}

    # 运行工作流
    print("\n=== 运行高级工作流 ===")
    result = advanced_graph.invoke({}, config)
    print(f"最终结果: {result}")

    # 查看所有状态
    print("\n=== 所有执行状态 ===")
    states = list(advanced_graph.get_state_history(config))
    for i, state in enumerate(states):
        print(f"状态 {i}: {state.values}")

    # 从中间状态分叉
    print("\n=== 从步骤2分叉 ===")
    step2_state = None
    for state in states:
        if state.values.get("step") == 2:
            step2_state = state
            break

    if step2_state:
        # 修改步骤2的数据
        branch_config = advanced_graph.update_state(
            step2_state.config, values={"data": "初始数据 -> 特殊处理"}
        )

        # 从分叉点继续
        branch_result = advanced_graph.invoke(None, branch_config)
        print(f"分叉结果: {branch_result}")

        # 比较两个分支
        print("\n=== 分支比较 ===")
        print(f"原始分支: {result}")
        print(f"新分支: {branch_result}")


def checkpoint_management_demo():
    """检查点管理演示"""
    print("\n" + "=" * 50)
    print("检查点管理演示")
    print("=" * 50)

    config = {"configurable": {"thread_id": "checkpoint_demo"}}

    # 创建多个检查点
    print("创建多个检查点...")
    for i in range(3):
        result = graph.invoke({}, config)
        print(f"运行 {i+1}: 主题={result.get('topic', '无')}")

    # 获取所有检查点
    print("\n=== 所有检查点 ===")
    states = list(graph.get_state_history(config))

    checkpoint_info = []
    for i, state in enumerate(states):
        checkpoint_id = state.config["configurable"]["checkpoint_id"]
        checkpoint_info.append(
            {
                "index": i,
                "checkpoint_id": checkpoint_id,
                "values": state.values,
                "next": state.next,
            }
        )
        print(f"检查点 {i}: {checkpoint_id[:8]}... - {state.values}")

    # 选择特定检查点恢复
    print("\n=== 恢复到特定检查点 ===")
    if len(checkpoint_info) >= 2:
        target_checkpoint = checkpoint_info[1]  # 选择第二个检查点
        target_config = {
            "configurable": {
                "thread_id": config["configurable"]["thread_id"],
                "checkpoint_id": target_checkpoint["checkpoint_id"],
            }
        }

        print(f"恢复到检查点: {target_checkpoint['checkpoint_id'][:8]}...")

        # 从该检查点继续执行
        if target_checkpoint["next"]:
            continued_result = graph.invoke(None, target_config)
            print(f"继续执行结果: {continued_result}")
        else:
            print("该检查点已完成，无法继续执行")


if __name__ == "__main__":
    run_time_travel_demo()
    interactive_time_travel()
    advanced_time_travel_demo()
    checkpoint_management_demo()
