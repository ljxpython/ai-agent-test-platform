from typing import Annotated

from config import llm
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    conversation_context: dict


@tool
def remember_user_info(info: str) -> str:
    """记住用户信息"""
    # 这个工具会在智能体中使用，通过状态来存储信息
    return f"我会记住这个信息：{info}"


@tool
def recall_user_info(query: str) -> str:
    """回忆用户信息"""
    # 这个工具会从状态中检索信息
    return f"让我回忆一下关于'{query}'的信息..."


# 创建工具列表
tools = [remember_user_info, recall_user_info]

# 绑定工具到 LLM
llm_with_tools = llm.bind_tools(tools)


def enhanced_agent_node(state: CustomState):
    """增强的智能体节点，处理记忆功能"""
    messages = state["messages"]
    context = state.get("conversation_context", {})

    # 分析最新消息中的信息
    if messages:
        last_message = messages[-1]
        if hasattr(last_message, "type") and last_message.type == "human":
            content = last_message.content if hasattr(last_message, "content") else ""

            # 提取用户信息
            if "我叫" in content or "名字是" in content:
                import re

                name_match = re.search(r"(?:我叫|名字是)(.+)", content)
                if name_match:
                    name = name_match.group(1).strip()
                    context["user_name"] = name

            # 提取偏好信息
            if "我喜欢" in content:
                preferences = context.get("preferences", [])
                preference = content.replace("我喜欢", "").strip()
                if preference not in preferences:
                    preferences.append(preference)
                    context["preferences"] = preferences

    # 构建增强的系统提示
    system_prompt = "你是一个有记忆能力的助手。"

    if context.get("user_name"):
        system_prompt += f" 用户的名字是{context['user_name']}。"

    if context.get("preferences"):
        prefs = ", ".join(context["preferences"])
        system_prompt += f" 用户喜欢：{prefs}。"

    # 添加系统消息
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages

    # 调用 LLM
    response = llm_with_tools.invoke(enhanced_messages)

    # 更新状态
    return {"messages": [response], "conversation_context": context}


# 导入工具节点和条件
from langgraph.prebuilt import ToolNode, tools_condition

# 创建工具节点
tool_node = ToolNode(tools)

# 构建图
graph_builder = StateGraph(CustomState)
graph_builder.add_node("agent", enhanced_agent_node)
graph_builder.add_node("tools", tool_node)

# 添加条件边：如果 LLM 调用工具，则执行工具；否则结束
graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("tools", "agent")  # 工具执行后回到智能体
graph_builder.add_edge(START, "agent")

# 编译图
graph = graph_builder.compile()


def run_short_term_memory_demo():
    """运行短期记忆演示"""
    print("短期记忆演示启动！")
    print("这个智能体可以在对话中记住和回忆信息。")
    print("试试说：'我叫张三'，然后问：'我的名字是什么？'")
    print("输入 'quit' 退出。")

    # 初始状态
    initial_state = {"messages": [], "user_name": "", "conversation_context": {}}

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 添加用户消息
            initial_state["messages"].append({"role": "user", "content": user_input})

            # 调用智能体
            result = graph.invoke(initial_state)

            # 更新状态
            initial_state.update(result)

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

            # 显示当前记忆的信息
            context = initial_state.get("conversation_context", {})
            if context:
                print(f"[记忆] {context}")

        except Exception as e:
            print(f"处理错误: {e}")


def memory_persistence_demo():
    """记忆持久化演示"""
    print("\n" + "=" * 50)
    print("记忆持久化演示")
    print("=" * 50)

    # 模拟多轮对话，展示记忆的累积
    conversations = [
        "我叫李明，是一名教师",
        "我喜欢阅读和旅行",
        "我住在北京",
        "你还记得我的职业吗？",
        "我的爱好是什么？",
        "我住在哪里？",
    ]

    state = {"messages": [], "user_name": "", "conversation_context": {}}

    for i, user_input in enumerate(conversations, 1):
        print(f"\n=== 对话轮次 {i} ===")
        print(f"用户: {user_input}")

        # 添加用户消息
        state["messages"].append({"role": "user", "content": user_input})

        # 处理
        result = graph.invoke(state)
        state.update(result)

        # 输出回复
        if result.get("messages"):
            assistant_message = result["messages"][-1]
            print(f"助手: {assistant_message.content}")

        # 显示当前记忆状态
        context = state.get("conversation_context", {})
        if context:
            print(f"[当前记忆] {context}")


def memory_types_demo():
    """不同类型记忆演示"""
    print("\n" + "=" * 50)
    print("不同类型记忆演示")
    print("=" * 50)

    class AdvancedMemoryState(TypedDict):
        messages: Annotated[list, lambda x, y: x + y]
        personal_info: dict  # 个人信息记忆
        preferences: dict  # 偏好记忆
        facts: dict  # 事实记忆
        episodic: list  # 情节记忆

    def advanced_memory_processor(state: AdvancedMemoryState):
        """高级记忆处理器"""
        messages = state["messages"]

        if not messages:
            return {}

        last_message = messages[-1]
        if not (hasattr(last_message, "type") and last_message.type == "human"):
            return {}

        content = last_message.content if hasattr(last_message, "content") else ""

        # 更新不同类型的记忆
        updates = {}

        # 个人信息记忆
        personal_info = state.get("personal_info", {})
        if "我叫" in content:
            import re

            name_match = re.search(r"我叫(.+)", content)
            if name_match:
                personal_info["name"] = name_match.group(1).strip()
                updates["personal_info"] = personal_info

        # 偏好记忆
        preferences = state.get("preferences", {})
        if "我喜欢" in content:
            pref = content.replace("我喜欢", "").strip()
            if "likes" not in preferences:
                preferences["likes"] = []
            if pref not in preferences["likes"]:
                preferences["likes"].append(pref)
                updates["preferences"] = preferences

        # 事实记忆
        facts = state.get("facts", {})
        if "今天" in content and ("天气" in content or "温度" in content):
            facts["today_weather"] = content
            updates["facts"] = facts

        # 情节记忆
        episodic = state.get("episodic", [])
        episodic.append(
            {"timestamp": len(episodic) + 1, "content": content, "type": "user_input"}
        )
        updates["episodic"] = episodic

        # 生成回复
        response_parts = ["我明白了。"]

        if updates.get("personal_info"):
            name = updates["personal_info"].get("name")
            if name:
                response_parts.append(f"你的名字是{name}。")

        if updates.get("preferences"):
            likes = updates["preferences"].get("likes", [])
            if likes:
                response_parts.append(f"你喜欢：{', '.join(likes)}。")

        response = " ".join(response_parts)
        updates["messages"] = [{"role": "assistant", "content": response}]

        return updates

    # 构建高级记忆图
    advanced_graph = StateGraph(AdvancedMemoryState)
    advanced_graph.add_node("memory_processor", advanced_memory_processor)
    advanced_graph.add_edge(START, "memory_processor")
    advanced_graph.add_edge("memory_processor", END)

    compiled_graph = advanced_graph.compile()

    # 测试高级记忆
    test_inputs = [
        "我叫王小明",
        "我喜欢编程",
        "我喜欢音乐",
        "今天天气很好",
        "你记得我的名字吗？",
        "我都喜欢什么？",
    ]

    state = {
        "messages": [],
        "personal_info": {},
        "preferences": {},
        "facts": {},
        "episodic": [],
    }

    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n--- 输入 {i}: {user_input} ---")

        state["messages"].append({"role": "user", "content": user_input})
        result = compiled_graph.invoke(state)
        state.update(result)

        if result.get("messages"):
            print(f"回复: {result['messages'][-1]['content']}")

        # 显示记忆状态
        print("记忆状态:")
        print(f"  个人信息: {state.get('personal_info', {})}")
        print(f"  偏好: {state.get('preferences', {})}")
        print(f"  事实: {state.get('facts', {})}")
        print(f"  情节数量: {len(state.get('episodic', []))}")


if __name__ == "__main__":
    run_short_term_memory_demo()
    memory_persistence_demo()
    memory_types_demo()
