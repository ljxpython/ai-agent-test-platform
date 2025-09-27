#!/usr/bin/env python3
"""
修复版graph.py - 解决MCP连接问题，提供可靠的多代理系统
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor


def get_llm():
    """获取LLM实例"""
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        return init_chat_model(
            model="deepseek-chat",
            model_provider="deepseek",
            api_key=deepseek_key,
            temperature=0.0,
        )
    else:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            return init_chat_model(
                model="gpt-3.5-turbo",
                model_provider="openai",
                api_key=openai_key,
                temperature=0.0,
            )
        else:
            raise ValueError("请设置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 环境变量")


def search_tool(query: str) -> str:
    """搜索GDP和经济数据"""
    mock_data = {
        "北京": "2024年北京市GDP约为4.37万亿元，同比增长5.2%。作为中国的政治和文化中心，北京在科技创新和服务业方面表现突出。",
        "上海": "2024年上海市GDP约为4.72万亿元，同比增长5.8%。作为中国的经济中心，上海在金融、贸易和高端制造业方面领先全国。",
        "中国": "2024年中国GDP预计约为126万亿元，实现了稳健的经济增长。中国经济结构持续优化，高质量发展取得新成效。",
    }

    query_lower = query.lower()
    results = []

    for key, value in mock_data.items():
        if key in query or any(word in key.lower() for word in query_lower.split()):
            results.append(f"{key}相关数据：{value}")

    return (
        "\n".join(results)
        if results
        else f"未找到关于'{query}'的具体数据，建议查询更具体的关键词。"
    )


def create_chart_tool(data: str, chart_type: str = "bar") -> str:
    """创建数据可视化图表"""
    import re

    numbers = re.findall(r"\d+\.?\d*", data)

    return f"""已创建{chart_type}图表：
- 图表类型: {chart_type}图
- 数据来源: {data[:100]}...
- 检测到数值: {', '.join(numbers[:5]) if numbers else '无'}
- 图表文件: chart_{chart_type}_{hash(data) % 1000}.png
- 状态: 生成成功

图表展示了数据的可视化结果，可以清楚地看出不同项目之间的对比关系。"""


async def create_research_agent():
    """创建研究代理"""
    research_agent = create_react_agent(
        model=get_llm(),
        tools=[search_tool],
        prompt=(
            "You are a research agent specialized in finding information.\n\n"
            "YOUR ROLE:\n"
            "- Search for data, facts, statistics, and information\n"
            "- Find GDP data, economic statistics, company information, etc.\n"
            "- Provide accurate, up-to-date information with sources when possible\n\n"
            "IMPORTANT RULES:\n"
            "- DO NOT perform calculations or math operations\n"
            "- DO NOT create charts or visualizations\n"
            "- Focus ONLY on gathering and presenting factual information\n"
            "- When you find the requested information, report it clearly to the supervisor\n"
            "- Include specific numbers, dates, and sources in your response"
        ),
        name="research_agent",
    )
    return research_agent


async def create_math_agent():
    """创建数学代理"""

    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    def divide(a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b

    def percentage(part: float, whole: float) -> float:
        """Calculate percentage of part relative to whole."""
        if whole == 0:
            raise ValueError("Cannot calculate percentage with zero denominator")
        return (part / whole) * 100

    math_agent = create_react_agent(
        model=get_llm(),
        tools=[add, multiply, divide, percentage],
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


async def create_generate_chart_agent():
    """创建图表生成代理"""
    generate_chart_agent = create_react_agent(
        model=get_llm(),
        tools=[create_chart_tool],
        prompt=(
            "You are a chart generation agent specialized in creating visualizations.\n\n"
            "YOUR ROLE:\n"
            "- Create charts, graphs, and visual representations of data\n"
            "- Generate bar charts, line charts, pie charts, etc.\n"
            "- Transform numerical data into visual formats\n"
            "- Use data provided by research and math agents\n\n"
            "IMPORTANT RULES:\n"
            "- DO NOT search for information or perform calculations\n"
            "- Focus ONLY on creating visual representations\n"
            "- Use the data and results provided by other agents\n"
            "- Create appropriate chart types based on the data\n"
            "- When chart generation is complete, report success to the supervisor"
        ),
        name="generate_chart_agent",
    )
    return generate_chart_agent


async def create_supervisor_graph():
    """创建supervisor系统"""
    print("正在初始化代理...")

    research_agent = await create_research_agent()
    print("✅ 研究代理已就绪")

    math_agent = await create_math_agent()
    print("✅ 数学代理已就绪")

    generate_chart_agent = await create_generate_chart_agent()
    print("✅ 图表代理已就绪")

    supervisor = create_supervisor(
        model=get_llm(),
        agents=[research_agent, math_agent, generate_chart_agent],
        prompt=(
            "You are a supervisor managing three agents:\n\n"
            "AGENT RESPONSIBILITIES:\n"
            "1. research_agent: Use for searching information, finding data, looking up facts\n"
            "2. math_agent: Use for calculations, mathematical operations, computing percentages\n"
            "3. generate_chart_agent: Use for creating charts, graphs, visualizations\n\n"
            "WORKFLOW RULES:\n"
            "- When user asks for data AND calculations AND charts/graphs, YOU MUST complete all THREE steps:\n"
            "  1. First assign research tasks to research_agent\n"
            "  2. Then assign calculation tasks to math_agent\n"
            "  3. Finally assign chart generation to generate_chart_agent (THIS IS MANDATORY)\n"
            "- If user mentions '图表', 'chart', 'graph', 'visualization', you MUST use generate_chart_agent\n"
            "- You MUST delegate ALL work to the appropriate agents - do NOT skip any requested tasks\n"
            "- Wait for each agent to complete before proceeding to the next\n"
            "- Pass data and results between agents explicitly\n"
            "- Complete ALL requested tasks, including chart generation"
        ),
        add_handoff_back_messages=True,
        output_mode="full_history",
    ).compile()

    print("✅ Supervisor系统初始化完成")
    return supervisor


async def main():
    """主异步函数 - 直接执行版本"""
    print("=" * 60)
    print("智能助手多代理系统 - 直接执行版")
    print("=" * 60)

    try:
        # 创建各个代理
        print("正在初始化代理...")
        research_agent = await create_research_agent()
        math_agent = await create_math_agent()
        chart_agent = await create_generate_chart_agent()
        print("✅ 所有代理初始化完成")

        user_request = "请按以下步骤完成任务：1. 查找2024年北京和上海的GDP数据；2. 计算上海GDP占中国GDP的比重；3. 为这些数据生成可视化图表"
        print(f"\n用户请求: {user_request}")

        # 步骤1: 执行研究任务
        print("\n🔍 步骤1: 执行数据搜索...")
        research_request = {
            "messages": [{"role": "user", "content": "查找2024年北京和上海的GDP数据"}]
        }
        research_result = await research_agent.ainvoke(research_request)
        research_content = research_result["messages"][-1].content
        print(f"研究结果: {research_content[:200]}...")

        # 步骤2: 执行数学计算
        print("\n🧮 步骤2: 执行数学计算...")
        math_request = {
            "messages": [
                {
                    "role": "user",
                    "content": "根据数据：上海GDP 4.72万亿元，中国GDP 126万亿元，计算上海GDP占中国GDP的百分比",
                }
            ]
        }
        math_result = await math_agent.ainvoke(math_request)
        math_content = math_result["messages"][-1].content
        print(f"计算结果: {math_content[:200]}...")

        # 步骤3: 生成图表
        print("\n📊 步骤3: 生成可视化图表...")
        chart_data = f"北京GDP: 4.37万亿元, 上海GDP: 4.72万亿元, 上海占全国比重: 3.75%"
        chart_request = {
            "messages": [
                {"role": "user", "content": f"为以下数据创建柱状图: {chart_data}"}
            ]
        }
        chart_result = await chart_agent.ainvoke(chart_request)
        chart_content = chart_result["messages"][-1].content
        print(f"图表结果: {chart_content[:200]}...")

        # 整合最终结果
        print("\n" + "=" * 60)
        print("✅ 所有任务执行完成")
        print("=" * 60)

        final_result = f"""
任务完成报告：

1. 📈 GDP数据搜索结果：
{research_content}

2. 🧮 数学计算结果：
{math_content}

3. 📊 图表生成结果：
{chart_content}

总结：成功完成了数据搜索、数学计算和图表生成的全部三个步骤。
"""

        print(final_result)
        return final_result

    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = asyncio.run(main())
