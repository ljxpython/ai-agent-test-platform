from typing import Annotated

from config import llm
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt
from typing_extensions import TypedDict


class State(TypedDict):
    messages: Annotated[list, add_messages]


@tool
def human_assistance(query: str) -> str:
    """请求人工协助"""
    # 使用 interrupt 暂停执行，等待人工输入
    human_response = interrupt({"query": query})
    return human_response.get("data", "没有收到人工回复")


@tool
def sensitive_action(action: str) -> str:
    """执行敏感操作（需要人工确认）"""
    # 请求人工确认
    confirmation = interrupt(
        {"action": action, "message": f"是否确认执行操作: {action}？(yes/no)"}
    )

    if confirmation.get("data", "").lower() in ["yes", "y", "是", "确认"]:
        return f"已执行操作: {action}"
    else:
        return f"操作已取消: {action}"


@tool
def review_content(content: str) -> str:
    """内容审核工具"""
    # 简单的内容检查
    sensitive_words = ["删除", "重置", "格式化", "清空"]

    if any(word in content for word in sensitive_words):
        # 需要人工审核
        review_result = interrupt(
            {"content": content, "message": f"检测到敏感内容，需要人工审核: {content}"}
        )

        if review_result.get("data", "").lower() in ["approve", "通过", "同意"]:
            return f"内容已通过审核: {content}"
        else:
            return f"内容被拒绝: {content}"
    else:
        return f"内容自动通过: {content}"


# 设置工具
tools = [human_assistance, sensitive_action, review_content]
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    """聊天机器人节点"""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 创建检查点保存器（人机交互需要）
memory = InMemorySaver()

# 构建图
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

# 添加工具节点
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

# 添加边
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

# 编译图（启用检查点以支持中断）
graph = graph_builder.compile(checkpointer=memory)


def run_human_in_loop_demo():
    """运行人机交互演示"""
    print("人机交互演示启动！")
    print("这个机器人可以请求人工协助或确认。")
    print("当机器人暂停等待时，请提供相应的输入。")
    print("输入 'quit' 退出。")

    config = {"configurable": {"thread_id": "human_loop_1"}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 开始处理
            result = graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]}, config
            )

            # 检查是否有中断
            current_state = graph.get_state(config)

            if current_state.next:
                # 有中断，等待人工输入
                print("\n=== 需要人工输入 ===")

                # 获取中断信息
                if current_state.tasks:
                    task = current_state.tasks[0]
                    if hasattr(task, "interrupts") and task.interrupts:
                        interrupt_data = task.interrupts[0].value
                        print(f"请求: {interrupt_data}")

                # 获取人工输入
                human_input = input("请输入回复: ")

                # 继续执行
                graph.update_state(config, {"data": human_input})
                final_result = graph.invoke(None, config)

                # 输出最终回复
                if final_result.get("messages"):
                    assistant_message = final_result["messages"][-1]
                    print(f"助手: {assistant_message.content}")
            else:
                # 没有中断，直接输出回复
                if result.get("messages"):
                    assistant_message = result["messages"][-1]
                    print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")


def demo_approval_workflow():
    """演示审批工作流"""
    print("\n" + "=" * 50)
    print("审批工作流演示")
    print("=" * 50)

    config = {"configurable": {"thread_id": "approval_demo"}}

    # 测试用例
    test_cases = [
        "请帮我删除所有文件",  # 敏感操作
        "请审核这个内容：今天天气不错",  # 普通内容
        "我需要人工协助解决这个问题",  # 人工协助
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n=== 测试案例 {i}: {test_input} ===")

        try:
            # 处理请求
            result = graph.invoke(
                {"messages": [{"role": "user", "content": test_input}]}, config
            )

            # 检查是否需要人工干预
            state = graph.get_state(config)

            if state.next:
                print("⏸️  需要人工干预")

                # 模拟人工输入
                if "删除" in test_input:
                    human_response = "no"  # 拒绝删除操作
                elif "协助" in test_input:
                    human_response = "我来帮助你解决问题"
                else:
                    human_response = "approve"  # 批准内容

                print(f"🤖 模拟人工输入: {human_response}")

                # 继续执行
                graph.update_state(config, {"data": human_response})
                final_result = graph.invoke(None, config)

                if final_result.get("messages"):
                    print(f"✅ 最终结果: {final_result['messages'][-1].content}")
            else:
                print("✅ 自动处理完成")
                if result.get("messages"):
                    print(f"结果: {result['messages'][-1].content}")

        except Exception as e:
            print(f"❌ 处理错误: {e}")


def interactive_approval_demo():
    """交互式审批演示"""
    print("\n" + "=" * 50)
    print("交互式审批演示")
    print("=" * 50)
    print("这个演示会模拟真实的人工审批流程")

    config = {"configurable": {"thread_id": "interactive_approval"}}

    while True:
        print("\n选择测试场景:")
        print("1. 敏感操作确认")
        print("2. 内容审核")
        print("3. 人工协助请求")
        print("4. 自定义输入")
        print("0. 返回主菜单")

        choice = input("请选择 (0-4): ").strip()

        if choice == "0":
            break
        elif choice == "1":
            test_input = "请执行系统重置操作"
        elif choice == "2":
            test_input = "请审核这个内容：准备删除旧数据"
        elif choice == "3":
            test_input = "我遇到了技术问题，需要专家协助"
        elif choice == "4":
            test_input = input("请输入自定义内容: ")
        else:
            print("无效选择")
            continue

        print(f"\n处理请求: {test_input}")

        try:
            result = graph.invoke(
                {"messages": [{"role": "user", "content": test_input}]}, config
            )

            state = graph.get_state(config)

            if state.next:
                print("\n⏸️  系统暂停，等待人工决策...")

                # 显示中断信息
                if state.tasks and hasattr(state.tasks[0], "interrupts"):
                    interrupt_info = state.tasks[0].interrupts[0].value
                    print(f"📋 审批信息: {interrupt_info}")

                # 获取人工决策
                decision = input("\n👤 请输入您的决策: ")

                # 继续执行
                graph.update_state(config, {"data": decision})
                final_result = graph.invoke(None, config)

                if final_result.get("messages"):
                    print(f"\n✅ 处理完成: {final_result['messages'][-1].content}")
            else:
                if result.get("messages"):
                    print(f"\n✅ 自动处理: {result['messages'][-1].content}")

        except Exception as e:
            print(f"\n❌ 处理错误: {e}")


if __name__ == "__main__":
    run_human_in_loop_demo()
    demo_approval_workflow()
    interactive_approval_demo()
