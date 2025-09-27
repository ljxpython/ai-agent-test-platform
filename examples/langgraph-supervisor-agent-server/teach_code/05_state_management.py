import operator
from typing import Annotated, Optional

from config import llm
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ComplexState(TypedDict):
    # 消息历史
    messages: Annotated[list, add_messages]

    # 用户信息
    user_name: Optional[str]
    user_preferences: dict

    # 对话统计
    message_count: Annotated[int, operator.add]

    # 上下文信息
    current_topic: Optional[str]
    conversation_summary: str


def analyze_input(state: ComplexState):
    """分析用户输入"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None

    if not last_message:
        return {}

    user_content = last_message.content.lower()

    # 检测话题
    topics = {
        "天气": ["天气", "温度", "下雨", "晴天"],
        "技术": ["编程", "代码", "技术", "开发"],
        "生活": ["生活", "日常", "吃饭", "睡觉"],
    }

    detected_topic = None
    for topic, keywords in topics.items():
        if any(keyword in user_content for keyword in keywords):
            detected_topic = topic
            break

    return {"current_topic": detected_topic, "message_count": 1}


def generate_response(state: ComplexState):
    """生成回复"""
    messages = state["messages"]
    current_topic = state.get("current_topic")
    user_name = state.get("user_name", "朋友")

    # 构建系统提示
    system_prompt = f"你是一个友好的助手。"
    if current_topic:
        system_prompt += f" 当前话题是：{current_topic}。"
    if user_name != "朋友":
        system_prompt += f" 用户名是：{user_name}。"

    # 添加系统消息
    enhanced_messages = [{"role": "system", "content": system_prompt}] + messages

    response = llm.invoke(enhanced_messages)

    return {"messages": [response]}


def update_summary(state: ComplexState):
    """更新对话摘要"""
    messages = state["messages"]
    message_count = state.get("message_count", 0)

    if message_count > 0 and message_count % 5 == 0:
        # 每5条消息更新一次摘要
        recent_messages = messages[-10:]  # 最近10条消息

        summary_prompt = "请简要总结以下对话内容：\n"
        for msg in recent_messages:
            role = "用户" if msg.get("role") == "user" else "助手"
            summary_prompt += f"{role}: {msg.get('content', '')}\n"

        summary_response = llm.invoke([{"role": "user", "content": summary_prompt}])

        return {"conversation_summary": summary_response.content}

    return {}


# 构建图
graph_builder = StateGraph(ComplexState)
graph_builder.add_node("analyze", analyze_input)
graph_builder.add_node("respond", generate_response)
graph_builder.add_node("summarize", update_summary)

# 添加边
graph_builder.add_edge(START, "analyze")
graph_builder.add_edge("analyze", "respond")
graph_builder.add_edge("respond", "summarize")
graph_builder.add_edge("summarize", END)

# 编译图
graph = graph_builder.compile()


def run_state_management_demo():
    """运行状态管理演示"""
    print("状态管理演示启动！")
    print("这个聊天机器人会跟踪对话状态、话题和统计信息。")
    print("输入 'quit' 退出，输入 'status' 查看状态。")

    # 初始状态
    current_state = {
        "messages": [],
        "user_name": None,
        "user_preferences": {},
        "message_count": 0,
        "current_topic": None,
        "conversation_summary": "",
    }

    while True:
        user_input = input("\n用户: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("再见！")
            break

        if user_input.lower() == "status":
            print(f"\n=== 当前状态 ===")
            print(f"消息数量: {current_state.get('message_count', 0)}")
            print(f"当前话题: {current_state.get('current_topic', '无')}")
            print(f"用户名: {current_state.get('user_name', '未设置')}")
            if current_state.get("conversation_summary"):
                print(f"对话摘要: {current_state['conversation_summary']}")
            continue

        # 检查是否设置用户名
        if not current_state.get("user_name") and "我叫" in user_input:
            import re

            name_match = re.search(r"我叫(.+)", user_input)
            if name_match:
                current_state["user_name"] = name_match.group(1).strip()
                print(f"已记录您的名字：{current_state['user_name']}")

        # 添加用户消息到状态
        current_state["messages"].append({"role": "user", "content": user_input})

        try:
            # 运行图
            result = graph.invoke(current_state)

            # 更新状态
            current_state.update(result)
            print(current_state)

            # 输出回复
            if result.get("messages"):
                assistant_message = result["messages"][-1]
                print(f"助手: {assistant_message.content}")

        except Exception as e:
            print(f"处理错误: {e}")


if __name__ == "__main__":
    run_state_management_demo()
