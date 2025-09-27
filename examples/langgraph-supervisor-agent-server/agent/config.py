"""Configuration management for the supervisor agent system."""

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class LLMConfig:
    """Configuration for Language Learning Model."""

    provider: str
    model: str
    api_key: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None


@dataclass
class MCPServerConfig:
    """Configuration for MCP (Model Context Protocol) servers."""

    name: str
    transport: str
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[list] = None
    env: Optional[Dict[str, str]] = None


@dataclass
class AgentConfig:
    """Configuration for individual agents."""

    name: str
    prompt: str
    description: str


@dataclass
class SupervisorConfig:
    """Configuration for the supervisor agent."""

    prompt: str
    add_handoff_back_messages: bool = True
    output_mode: str = "full_history"


class Config:
    """Main configuration class for the supervisor agent system."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self.llm = self._load_llm_config()
        self.mcp_servers = self._load_mcp_servers_config()
        self.agents = self._load_agents_config()
        self.supervisor = self._load_supervisor_config()

    def _load_llm_config(self) -> LLMConfig:
        """Load LLM configuration from environment variables."""
        return LLMConfig(
            provider=os.getenv("LLM_PROVIDER", "deepseek"),
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
            max_tokens=(
                int(os.getenv("LLM_MAX_TOKENS"))
                if os.getenv("LLM_MAX_TOKENS")
                else None
            ),
        )

    def _load_mcp_servers_config(self) -> Dict[str, MCPServerConfig]:
        """Load MCP servers configuration."""
        return {
            "search_api": MCPServerConfig(
                name="search1api-mcp",
                transport="stdio",
                command="npx",
                args=["-y", "search1api-mcp", "stdio"],
                env={"SEARCH1API_KEY": os.getenv("SEARCH1API_KEY", "")},
            ),
            "zhipu_search": MCPServerConfig(
                name="zhipu-mcp",
                transport="sse",
                url=f"https://open.bigmodel.cn/api/mcp/web_search/sse?Authorization={os.getenv('ZHIPU_API_KEY', '')}",
            ),
            "chart_generator": MCPServerConfig(
                name="chart-mcp",
                transport="sse",
                url=os.getenv("CHART_MCP_URL", "http://localhost:1122/sse"),
            ),
        }

    def _load_agents_config(self) -> Dict[str, AgentConfig]:
        """Load agents configuration."""
        return {
            "research": AgentConfig(
                name="research_agent",
                description="专门负责查找信息和数据的智能体",
                prompt=(
                    "你是一个专门负责查找信息的研究智能体。\n\n"
                    "你的职责：\n"
                    "- 搜索数据、事实、统计信息和各类信息\n"
                    "- 查找GDP数据、经济统计、公司信息等\n"
                    "- 尽可能提供准确、最新的信息并注明来源\n\n"
                    "重要规则：\n"
                    "- 不要进行计算或数学运算\n"
                    "- 不要创建图表或可视化内容\n"
                    "- 只专注于收集和呈现事实信息\n"
                    "- 找到所需信息后，清楚地向监督者报告\n"
                    "- 在回复中包含具体的数字、日期和信息来源"
                ),
            ),
            "math": AgentConfig(
                name="math_agent",
                description="专门负责数学计算的智能体",
                prompt=(
                    "你是一个专门负责计算的数学智能体。\n\n"
                    "你的职责：\n"
                    "- 执行数学计算和运算\n"
                    "- 计算百分比、比率、比例\n"
                    "- 处理其他智能体提供的数值数据\n"
                    "- 提供精确的数值结果\n\n"
                    "重要规则：\n"
                    "- 不要搜索信息或数据\n"
                    "- 不要创建图表或可视化内容\n"
                    "- 只专注于数学计算\n"
                    "- 清楚地展示你的计算步骤\n"
                    "- 计算完成后，向监督者报告结果"
                ),
            ),
            "chart": AgentConfig(
                name="generate_chart_agent",
                description="专门负责创建可视化图表的智能体",
                prompt=(
                    "你是一个专门负责创建可视化图表的智能体。\n\n"
                    "你的职责：\n"
                    "- 创建图表、图形和数据的可视化表示\n"
                    "- 生成柱状图、折线图、饼图等\n"
                    "- 将数值数据转换为可视化格式\n"
                    "- 使用研究智能体和数学智能体提供的数据\n\n"
                    "重要规则：\n"
                    "- 不要搜索信息或执行计算\n"
                    "- 只专注于创建可视化表示\n"
                    "- 使用其他智能体提供的数据和结果\n"
                    "- 根据数据创建合适的图表类型\n"
                    "- 图表生成完成后，向监督者报告成功"
                ),
            ),
        }

    def _load_supervisor_config(self) -> SupervisorConfig:
        """Load supervisor configuration."""
        return SupervisorConfig(
            prompt=(
                "你是一个管理三个智能体的监督者：\n\n"
                "智能体职责：\n"
                "1. research_agent（研究智能体）：用于搜索信息、查找数据、查询事实\n"
                "2. math_agent（数学智能体）：用于计算、数学运算、计算百分比\n"
                "3. generate_chart_agent（图表生成智能体）：用于创建图表、图形、可视化\n\n"
                "工作流程规则：\n"
                "- 当用户要求数据、计算和图表/图形时，按以下顺序执行：\n"
                "  1. 首先将研究任务分配给 research_agent\n"
                "  2. 然后将计算任务分配给 math_agent\n"
                "  3. 最后将图表生成分配给 generate_chart_agent\n"
                "- 如果用户提到'图表'、'chart'、'graph'、'visualization'，总是使用 generate_chart_agent\n"
                "- 一次只分配工作给一个智能体，等待完成后再继续\n"
                "- 不要自己做任何工作，总是委托给合适的智能体\n"
                "- 明确说明要在智能体之间传递什么数据/结果"
            ),
            add_handoff_back_messages=True,
            output_mode="full_history",
        )

    def validate(self) -> None:
        """Validate configuration and raise errors for missing required values."""
        if not self.llm.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")

        # Validate MCP server configurations
        for server_name, server_config in self.mcp_servers.items():
            if server_config.transport == "sse" and not server_config.url:
                raise ValueError(f"URL is required for SSE transport in {server_name}")
            elif server_config.transport == "stdio" and not server_config.command:
                raise ValueError(
                    f"Command is required for stdio transport in {server_name}"
                )


# Global configuration instance
config = Config()
