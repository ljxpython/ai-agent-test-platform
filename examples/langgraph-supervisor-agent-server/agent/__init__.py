"""
Supervisor Agent System

A professional multi-agent system built with LangGraph that manages specialized agents
for research, mathematics, and chart generation tasks.

Main Components:
- SupervisorAgent: Coordinates multiple specialized agents
- ResearchAgent: Handles information gathering and data search
- MathAgent: Performs mathematical calculations and operations
- ChartAgent: Creates visualizations and charts

Usage:
    from agent import SupervisorGraph, process_user_request

    # Simple usage
    result = await process_user_request("Find GDP data for China 2024")

    # Advanced usage
    supervisor = SupervisorGraph()
    await supervisor.initialize()
    async for chunk in await supervisor.process_request("Your request here"):
        print(chunk)
"""

from .agents import AgentManager, LocalToolAgentFactory, MathTools, MCPAgentFactory
from .config import Config, config
from .exceptions import (
    AgentCreationError,
    ConfigurationError,
    MCPConnectionError,
    RequestProcessingError,
    ServiceNotAvailableError,
    SupervisorAgentError,
    SupervisorInitializationError,
    ToolExecutionError,
    ValidationError,
)
from .graph import graph  # Legacy support
from .graph import (
    SupervisorGraph,
    create_supervisor_graph,
    get_supervisor_graph,
    get_system_info,
    process_user_request,
)
from .logging_config import get_logger, setup_logging
from .supervisor import SupervisorAgent, SupervisorService, supervisor_service

__version__ = "1.0.0"
__author__ = "Supervisor Agent Team"

__all__ = [
    # Main classes
    "SupervisorGraph",
    "SupervisorAgent",
    "SupervisorService",
    "AgentManager",
    # Factory classes
    "MCPAgentFactory",
    "LocalToolAgentFactory",
    # Utility classes
    "MathTools",
    "Config",
    # Functions
    "get_supervisor_graph",
    "create_supervisor_graph",
    "process_user_request",
    "get_system_info",
    "setup_logging",
    "get_logger",
    # Instances
    "config",
    "supervisor_service",
    "graph",  # Legacy support
    # Exceptions
    "SupervisorAgentError",
    "ConfigurationError",
    "AgentCreationError",
    "MCPConnectionError",
    "SupervisorInitializationError",
    "RequestProcessingError",
    "ToolExecutionError",
    "ValidationError",
    "ServiceNotAvailableError",
]
