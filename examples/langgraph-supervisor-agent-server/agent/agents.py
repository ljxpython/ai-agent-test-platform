"""Agent factory and management for the supervisor agent system."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from .config import AgentConfig, MCPServerConfig, config

logger = logging.getLogger(__name__)


class AgentFactory(ABC):
    """Abstract base class for agent factories."""

    @abstractmethod
    async def create_agent(self, agent_config: AgentConfig) -> Any:
        """Create an agent based on the provided configuration."""
        pass


class MCPAgentFactory(AgentFactory):
    """Factory for creating agents that use MCP (Model Context Protocol) tools."""

    def __init__(self, mcp_server_config: MCPServerConfig, llm_model: Any):
        """Initialize the MCP agent factory.

        Args:
            mcp_server_config: Configuration for the MCP server
            llm_model: The language model to use for the agent
        """
        self.mcp_server_config = mcp_server_config
        self.llm_model = llm_model
        self._client: Optional[MultiServerMCPClient] = None

    async def _get_mcp_client(self) -> MultiServerMCPClient:
        """Get or create MCP client."""
        if self._client is None:
            server_config = self._build_server_config()
            self._client = MultiServerMCPClient(server_config)
            logger.info(f"Created MCP client for {self.mcp_server_config.name}")
        return self._client

    def _build_server_config(self) -> Dict[str, Dict[str, Any]]:
        """Build server configuration for MultiServerMCPClient."""
        config_dict = {"transport": self.mcp_server_config.transport}

        if self.mcp_server_config.url:
            config_dict["url"] = self.mcp_server_config.url

        if self.mcp_server_config.command:
            config_dict["command"] = self.mcp_server_config.command

        if self.mcp_server_config.args:
            config_dict["args"] = self.mcp_server_config.args

        if self.mcp_server_config.env:
            config_dict["env"] = self.mcp_server_config.env

        return {self.mcp_server_config.name: config_dict}

    async def create_agent(self, agent_config: AgentConfig) -> Any:
        """Create an MCP-based agent."""
        try:
            client = await self._get_mcp_client()
            tools = await client.get_tools()

            agent = create_react_agent(
                model=self.llm_model,
                tools=tools,
                prompt=agent_config.prompt,
                name=agent_config.name,
            )

            logger.info(f"Created MCP agent: {agent_config.name}")
            return agent

        except Exception as e:
            logger.error(f"Failed to create MCP agent {agent_config.name}: {e}")
            raise


class LocalToolAgentFactory(AgentFactory):
    """Factory for creating agents that use local tools."""

    def __init__(self, llm_model: Any, tools: List[Any]):
        """Initialize the local tool agent factory.

        Args:
            llm_model: The language model to use for the agent
            tools: List of tools to provide to the agent
        """
        self.llm_model = llm_model
        self.tools = tools

    async def create_agent(self, agent_config: AgentConfig) -> Any:
        """Create a local tool-based agent."""
        try:
            agent = create_react_agent(
                model=self.llm_model,
                tools=self.tools,
                prompt=agent_config.prompt,
                name=agent_config.name,
            )

            logger.info(f"Created local tool agent: {agent_config.name}")
            return agent

        except Exception as e:
            logger.error(f"Failed to create local tool agent {agent_config.name}: {e}")
            raise


class MathTools:
    """Collection of mathematical tools for the math agent."""

    @staticmethod
    def add(a: float, b: float) -> float:
        """Add two numbers."""
        return a + b

    @staticmethod
    def subtract(a: float, b: float) -> float:
        """Subtract two numbers."""
        return a - b

    @staticmethod
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers."""
        return a * b

    @staticmethod
    def divide(a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    @staticmethod
    def percentage(part: float, total: float) -> float:
        """Calculate percentage."""
        if total == 0:
            raise ValueError("Total cannot be zero for percentage calculation")
        return (part / total) * 100

    @staticmethod
    def ratio(a: float, b: float) -> float:
        """Calculate ratio of a to b."""
        if b == 0:
            raise ValueError("Denominator cannot be zero for ratio calculation")
        return a / b


class AgentManager:
    """Manager for creating and managing all agents in the system."""

    def __init__(self):
        """Initialize the agent manager."""
        self.llm_model = self._initialize_llm()
        self.agents: Dict[str, Any] = {}
        logger.info("AgentManager initialized")

    def _initialize_llm(self) -> Any:
        """Initialize the language model."""
        try:
            model = init_chat_model(f"{config.llm.provider}:{config.llm.model}")
            logger.info(f"Initialized LLM: {config.llm.provider}:{config.llm.model}")
            return model
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            raise

    async def create_research_agent(self) -> Any:
        """Create the research agent using Zhipu MCP server."""
        factory = MCPAgentFactory(config.mcp_servers["zhipu_search"], self.llm_model)
        agent = await factory.create_agent(config.agents["research"])
        self.agents["research"] = agent
        return agent

    async def create_math_agent(self) -> Any:
        """Create the math agent using local tools."""
        math_tools = [
            MathTools.add,
            MathTools.subtract,
            MathTools.multiply,
            MathTools.divide,
            MathTools.percentage,
            MathTools.ratio,
        ]

        factory = LocalToolAgentFactory(self.llm_model, math_tools)
        agent = await factory.create_agent(config.agents["math"])
        self.agents["math"] = agent
        return agent

    async def create_chart_agent(self) -> Any:
        """Create the chart generation agent using chart MCP server."""
        factory = MCPAgentFactory(config.mcp_servers["chart_generator"], self.llm_model)
        agent = await factory.create_agent(config.agents["chart"])
        self.agents["chart"] = agent
        return agent

    async def create_all_agents(self) -> Dict[str, Any]:
        """Create all agents and return them as a dictionary."""
        try:
            research_agent = await self.create_research_agent()
            math_agent = await self.create_math_agent()
            chart_agent = await self.create_chart_agent()

            agents = {
                "research": research_agent,
                "math": math_agent,
                "chart": chart_agent,
            }

            logger.info("All agents created successfully")
            return agents

        except Exception as e:
            logger.error(f"Failed to create agents: {e}")
            raise

    def get_agent(self, agent_name: str) -> Optional[Any]:
        """Get an agent by name."""
        return self.agents.get(agent_name)

    def list_agents(self) -> List[str]:
        """List all available agent names."""
        return list(self.agents.keys())
