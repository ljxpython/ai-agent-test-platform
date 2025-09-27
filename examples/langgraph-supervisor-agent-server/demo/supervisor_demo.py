import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_deepseek import ChatDeepSeek
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Send
from typing_extensions import TypedDict

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

llm = init_chat_model(
    model="deepseek-chat",
    model_provider="deepseek",
    api_key=api_key,
)

from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor


async def create_math_agent():
    def add(a: float, b: float):
        """Add two numbers."""
        return a + b

    def multiply(a: float, b: float):
        """Multiply two numbers."""
        return a * b

    def divide(a: float, b: float):
        """Divide two numbers."""
        return a / b

    math_agent = create_react_agent(
        model=llm,
        tools=[add, multiply, divide],
        prompt=(
            "You are a math agent specialized in calculations.\n\n"
            "YOUR ROLE:\n"
            "- Perform mathematical calculations and operations\n"
            "- Calculate percentages, ratios, proportions\n"
            "- Process numerical data provided by other agents\n"
            "- Provide precise numerical results\n\n"
            "IMPORTANT RULES:\n"
            "- DO NOT search for information or data\n"
            "- DO NOT create charts or visualizations\n"
            "- Focus ONLY on mathematical computations\n"
            "- Show your calculation steps clearly\n"
            "- When calculations are complete, report results to the supervisor"
        ),
        name="math_agent",
    )
    return math_agent


async def create_research_agent_v1():
    """创建研究代理的异步函数"""

    client = MultiServerMCPClient(
        {
            "search1api-mcp": {
                "command": "npx",
                "args": ["-y", "search1api-mcp", "stdio"],
                "transport": "stdio",
                "env": {"SEARCH1API_KEY": "A0A335D4-000C-4F4A-8F0E-7A587BA00A8M"},
            },
        }
    )

    # 异步获取工具
    tools = await client.get_tools()

    research_agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=(
            "You are a research agent.\n\n"
            "INSTRUCTIONS:\n"
            "- Assist ONLY with research-related tasks, DO NOT do any math\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        ),
        name="research_agent",
    )

    return research_agent


async def build_supervisor_system():
    """构建监督者多智能体系统"""
    research_tools = await create_research_agent_v1()
    math_tools = await create_math_agent()

    # 1. 创建专门智能体
    research_agent = create_react_agent(
        model=llm,
        tools=research_tools,
        prompt="你是研究智能体，专门负责信息搜索...",
        name="research_agent",
    )

    math_agent = create_react_agent(
        model=llm,
        tools=math_tools,
        prompt="你是数学智能体，专门负责计算...",
        name="math_agent",
    )

    # 2. 创建监督者
    supervisor = create_supervisor(
        model=llm,
        agents=[research_agent, math_agent],
        prompt="""
        你是监督者，负责协调研究智能体和数学智能体：
        - 分析用户需求
        - 分配任务给合适的智能体
        - 整合结果
        """,
        add_handoff_back_messages=True,
        output_mode="full_history",
    )

    return supervisor.compile()


import operator


def build_customer_service_bot():
    """构建智能客服系统"""

    class CustomerServiceState(TypedDict):
        user_message: str
        intent: str
        entities: dict
        response: str
        escalate_to_human: bool
        conversation_history: Annotated[list, operator.add]

    def intent_recognition(state: CustomerServiceState) -> dict:
        """意图识别"""
        message = state["user_message"]

        # 简化的意图识别
        if "退款" in message or "refund" in message.lower():
            intent = "refund_request"
        elif "订单" in message or "order" in message.lower():
            intent = "order_inquiry"
        elif "技术" in message or "technical" in message.lower():
            intent = "technical_support"
        else:
            intent = "general_inquiry"

        return {"intent": intent}

    def handle_refund(state: CustomerServiceState) -> dict:
        """处理退款请求"""
        return {
            "response": "我来帮您处理退款申请。请提供您的订单号。",
            "escalate_to_human": False,
        }

    def handle_order_inquiry(state: CustomerServiceState) -> dict:
        """处理订单查询"""
        return {
            "response": "请提供您的订单号，我来查询订单状态。",
            "escalate_to_human": False,
        }

    def handle_technical_support(state: CustomerServiceState) -> dict:
        """处理技术支持"""
        return {
            "response": "技术问题比较复杂，我为您转接技术专家。",
            "escalate_to_human": True,
        }

    def handle_general(state: CustomerServiceState) -> dict:
        """处理一般咨询"""
        return {"response": "感谢您的咨询，我来为您解答。", "escalate_to_human": False}

    def route_by_intent(state: CustomerServiceState) -> str:
        intent_map = {
            "refund_request": "handle_refund",
            "order_inquiry": "handle_order",
            "technical_support": "handle_technical",
            "general_inquiry": "handle_general",
        }
        return intent_map.get(state["intent"], "handle_general")

    # 构建工作流
    workflow = StateGraph(CustomerServiceState)
    workflow.add_node("intent_recognition", intent_recognition)
    workflow.add_node("handle_refund", handle_refund)
    workflow.add_node("handle_order", handle_order_inquiry)
    workflow.add_node("handle_technical", handle_technical_support)
    workflow.add_node("handle_general", handle_general)

    workflow.add_edge(START, "intent_recognition")
    workflow.add_conditional_edges(
        "intent_recognition",
        route_by_intent,
        {
            "handle_refund": "handle_refund",
            "handle_order": "handle_order",
            "handle_technical": "handle_technical",
            "handle_general": "handle_general",
        },
    )

    # 所有处理节点都连接到结束
    for node in ["handle_refund", "handle_order", "handle_technical", "handle_general"]:
        workflow.add_edge(node, END)

    return workflow.compile()


def main():
    supervisor = build_customer_service_bot()
    results = supervisor.invoke({"user_message": "我想退款"})
    print(results)
    results = supervisor.invoke({"user_message": "我想查询订单"})
    print(results)
    results = supervisor.invoke({"user_message": "我想咨询技术问题"})
    print(results)
    results = supervisor.invoke({"user_message": "我想咨询一般问题"})
    print(results)


if __name__ == "__main__":
    main()
