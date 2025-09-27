from config import llm
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import create_react_agent
from typing_extensions import Annotated, Literal, TypedDict


class SupervisorState(TypedDict):
    messages: Annotated[list, add_messages]
    next_agent: str
    task_complete: bool


@tool
def search_information(query: str) -> str:
    """搜索信息工具"""
    # 模拟搜索结果
    search_results = {
        "天气": "今天天气晴朗，温度适宜",
        "新闻": "今日重要新闻：科技发展迅速",
        "股票": "股市今日表现平稳",
        "体育": "足球比赛结果：主队获胜",
    }

    for key, result in search_results.items():
        if key in query:
            return f"搜索结果：{result}"

    return f"搜索'{query}'的结果：相关信息已找到"


@tool
def calculate_math(expression: str) -> str:
    """数学计算工具"""
    try:
        # 安全的数学计算
        allowed_chars = set("0123456789+-*/().")
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
        "文章": f"{topic}相关文章：\n这是一篇关于{topic}的深度分析...",
    }

    for key, template in content_templates.items():
        if key in topic:
            return template

    return f"已生成关于'{topic}'的内容"


@tool
def analyze_data(data: str) -> str:
    """数据分析工具"""
    # 简单的数据分析
    if "," in data:
        numbers = []
        for item in data.split(","):
            try:
                numbers.append(float(item.strip()))
            except ValueError:
                continue

        if numbers:
            avg = sum(numbers) / len(numbers)
            max_val = max(numbers)
            min_val = min(numbers)
            return f"数据分析结果：平均值={avg:.2f}, 最大值={max_val}, 最小值={min_val}"

    return f"已分析数据：{data}"


# 创建专门的智能体
research_agent = create_react_agent(
    model=llm,
    tools=[search_information],
    prompt="你是研究智能体，专门负责信息搜索和数据收集。",
    name="research_agent",
)

math_agent = create_react_agent(
    model=llm,
    tools=[calculate_math],
    prompt="你是数学智能体，专门负责数学计算和数值分析。",
    name="math_agent",
)

content_agent = create_react_agent(
    model=llm,
    tools=[generate_content],
    prompt="你是内容智能体，专门负责创作和内容生成。",
    name="content_agent",
)

analysis_agent = create_react_agent(
    model=llm,
    tools=[analyze_data],
    prompt="你是分析智能体，专门负责数据分析和统计。",
    name="analysis_agent",
)

# 修复消息处理逻辑 - 统一使用字典格式


def supervisor_node(state: SupervisorState):
    """监督者节点"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {"next_agent": "END", "task_complete": True}

    # 修复：处理消息对象或字典的兼容逻辑
    if hasattr(last_message, "content"):
        user_content = last_message.content.lower()
    elif isinstance(last_message, dict):
        user_content = last_message.get("content", "").lower()
    else:
        user_content = str(last_message).lower()

    # 分析任务类型并分配给合适的智能体
    if any(
        keyword in user_content for keyword in ["搜索", "查找", "信息", "新闻", "天气"]
    ):
        next_agent = "research_agent"
    elif any(
        keyword in user_content for keyword in ["计算", "数学", "加", "减", "乘", "除"]
    ):
        next_agent = "math_agent"
    elif any(
        keyword in user_content
        for keyword in ["写", "创作", "生成", "故事", "文章", "诗歌"]
    ):
        next_agent = "content_agent"
    elif any(keyword in user_content for keyword in ["分析", "统计", "数据", "平均"]):
        next_agent = "analysis_agent"
    else:
        # 默认使用研究智能体
        next_agent = "research_agent"

    # 添加监督者的分析消息
    supervisor_message = f"[监督者] 分析任务类型，分配给 {next_agent}"

    return {
        "messages": [{"role": "assistant", "content": supervisor_message}],
        "next_agent": next_agent,
        "task_complete": False,
    }


# 修复各智能体节点的消息处理 - 使用model_dump替代dict


def research_node(state: SupervisorState):
    """研究智能体节点"""
    result = research_agent.invoke(state)
    return {
        "messages": [
            (
                msg.model_dump()
                if hasattr(msg, "model_dump")
                else (msg.dict() if hasattr(msg, "dict") else msg)
            )
            for msg in result["messages"]
        ],
        "task_complete": True,
    }


def math_node(state: SupervisorState):
    """数学智能体节点"""
    result = math_agent.invoke(state)
    return {
        "messages": [
            (
                msg.model_dump()
                if hasattr(msg, "model_dump")
                else (msg.dict() if hasattr(msg, "dict") else msg)
            )
            for msg in result["messages"]
        ],
        "task_complete": True,
    }


def content_node(state: SupervisorState):
    """内容智能体节点"""
    result = content_agent.invoke(state)
    return {
        "messages": [
            (
                msg.model_dump()
                if hasattr(msg, "model_dump")
                else (msg.dict() if hasattr(msg, "dict") else msg)
            )
            for msg in result["messages"]
        ],
        "task_complete": True,
    }


def analysis_node(state: SupervisorState):
    """分析智能体节点"""
    result = analysis_agent.invoke(state)
    return {
        "messages": [
            (
                msg.model_dump()
                if hasattr(msg, "model_dump")
                else (msg.dict() if hasattr(msg, "dict") else msg)
            )
            for msg in result["messages"]
        ],
        "task_complete": True,
    }


# 修复路由函数的返回类型注解


def route_to_agent(
    state: SupervisorState,
) -> Literal["research_agent", "math_agent", "content_agent", "analysis_agent", "END"]:
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

# 添加边
supervisor_builder.add_edge(START, "supervisor")
supervisor_builder.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "research_agent": "research_agent",
        "math_agent": "math_agent",
        "content_agent": "content_agent",
        "analysis_agent": "analysis_agent",
        "END": END,
    },
)

# 所有智能体完成后返回监督者
supervisor_builder.add_edge("research_agent", END)
supervisor_builder.add_edge("math_agent", END)
supervisor_builder.add_edge("content_agent", END)
supervisor_builder.add_edge("analysis_agent", END)

# 编译图
supervisor_graph = supervisor_builder.compile()


# 修复演示函数中的消息处理逻辑
def run_supervisor_demo():
    """运行监督者模式演示"""
    print("监督者模式多智能体演示启动！")
    print("监督者会分析任务并分配给合适的专门智能体：")
    print("- 研究智能体：信息搜索")
    print("- 数学智能体：数学计算")
    print("- 内容智能体：内容创作")
    print("- 分析智能体：数据分析")
    print("输入 'quit' 退出。")

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        try:
            # 调用监督者图
            result = supervisor_graph.invoke(
                {"messages": [{"role": "user", "content": user_input}]}
            )

            # 修复：统一处理消息对象和字典
            for message in result["messages"]:
                # 获取消息内容和角色
                if hasattr(message, "content") and hasattr(message, "role"):
                    content = message.content
                    role = message.role
                elif isinstance(message, dict):
                    content = message.get("content", "")
                    role = message.get("role", "")
                else:
                    continue

                if role == "assistant":
                    if content.startswith("[监督者]"):
                        print(f"🎯 {content}")
                    else:
                        print(f"🤖 智能体回复: {content}")

        except Exception as e:
            print(f"处理错误: {e}")


def test_supervisor_routing():
    """测试监督者路由"""
    print("\n" + "=" * 50)
    print("监督者路由测试")
    print("=" * 50)

    test_cases = [
        ("搜索今天的天气信息", "research_agent"),
        ("计算 15 + 27 * 3", "math_agent"),
        ("写一个关于春天的故事", "content_agent"),
        ("分析数据：1,2,3,4,5", "analysis_agent"),
        ("查找最新的科技新闻", "research_agent"),
        ("生成一首诗歌", "content_agent"),
    ]

    for user_input, expected_agent in test_cases:
        print(f"\n测试输入: {user_input}")
        print(f"期望智能体: {expected_agent}")

        try:
            # 只运行监督者节点来测试路由
            result = supervisor_node(
                {
                    "messages": [{"role": "user", "content": user_input}],
                    "next_agent": "",
                    "task_complete": False,
                }
            )

            actual_agent = result["next_agent"]
            print(f"实际智能体: {actual_agent}")
            print(f"路由{'✅ 正确' if actual_agent == expected_agent else '❌ 错误'}")

        except Exception as e:
            print(f"测试错误: {e}")


def demo_multi_step_workflow():
    """演示多步骤工作流"""
    print("\n" + "=" * 50)
    print("多步骤工作流演示")
    print("=" * 50)

    # 模拟复杂任务的多步骤处理
    workflow_steps = [
        "搜索关于人工智能的最新信息",
        "分析数据：10,20,30,40,50",
        "计算平均值的两倍",
        "写一篇关于AI发展的简短文章",
    ]

    print("执行多步骤工作流:")
    for i, step in enumerate(workflow_steps, 1):
        print(f"\n=== 步骤 {i}: {step} ===")

        try:
            result = supervisor_graph.invoke(
                {"messages": [{"role": "user", "content": step}]}
            )

            # 修复：统一处理消息对象和字典
            for message in result["messages"]:
                # 获取消息内容和角色
                if hasattr(message, "content") and hasattr(message, "role"):
                    content = message.content
                    role = message.role
                elif isinstance(message, dict):
                    content = message.get("content", "")
                    role = message.get("role", "")
                else:
                    continue

                if role == "assistant":
                    if content.startswith("[监督者]"):
                        print(f"🎯 {content}")
                    else:
                        print(f"🤖 {content}")

        except Exception as e:
            print(f"步骤 {i} 错误: {e}")


def demo_agent_specialization():
    """演示智能体专业化"""
    print("\n" + "=" * 50)
    print("智能体专业化演示")
    print("=" * 50)

    # 测试每个智能体的专业能力
    agent_tests = [
        {
            "agent": "research_agent",
            "name": "研究智能体",
            "tests": ["搜索天气信息", "查找新闻", "获取股票信息"],
        },
        {
            "agent": "math_agent",
            "name": "数学智能体",
            "tests": ["计算 2+3", "计算 10*5", "计算 (8-3)*4"],
        },
        {
            "agent": "content_agent",
            "name": "内容智能体",
            "tests": ["写一个故事", "创作诗歌", "生成文章"],
        },
        {
            "agent": "analysis_agent",
            "name": "分析智能体",
            "tests": ["分析数据：1,2,3", "统计信息：5,10,15", "计算平均值：2,4,6"],
        },
    ]

    for agent_info in agent_tests:
        print(f"\n=== {agent_info['name']} 专业能力测试 ===")

        for test in agent_info["tests"]:
            print(f"\n测试: {test}")

            try:
                result = supervisor_graph.invoke(
                    {"messages": [{"role": "user", "content": test}]}
                )

                # 修复：统一处理消息对象和字典
                if result["messages"]:
                    first_message = result["messages"][0]
                    # 获取消息内容
                    if hasattr(first_message, "content"):
                        supervisor_msg = first_message.content
                    elif isinstance(first_message, dict):
                        supervisor_msg = first_message.get("content", "")
                    else:
                        supervisor_msg = str(first_message)

                    if agent_info["agent"] in supervisor_msg:
                        print("✅ 正确路由")
                    else:
                        print("❌ 路由错误")

                # 输出结果
                if len(result["messages"]) > 1:
                    last_message = result["messages"][-1]
                    # 获取消息内容
                    if hasattr(last_message, "content"):
                        final_result = last_message.content
                    elif isinstance(last_message, dict):
                        final_result = last_message.get("content", "")
                    else:
                        final_result = str(last_message)

                    print(f"结果: {final_result[:100]}...")

            except Exception as e:
                print(f"测试错误: {e}")


if __name__ == "__main__":
    run_supervisor_demo()
    test_supervisor_routing()
    demo_multi_step_workflow()
    demo_agent_specialization()
