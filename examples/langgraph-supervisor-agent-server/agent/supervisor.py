"""Supervisor agent implementation for managing multiple specialized agents."""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from langgraph_supervisor import create_supervisor

from .agents import AgentManager
from .config import config

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Supervisor agent that manages and coordinates multiple specialized agents."""

    def __init__(self):
        """Initialize the supervisor agent."""
        self.agent_manager = AgentManager()
        self.supervisor_graph = None
        self._agents: Dict[str, Any] = {}
        logger.info("SupervisorAgent initialized")

    async def initialize(self) -> None:
        """Initialize the supervisor and all managed agents."""
        try:
            # Validate configuration
            config.validate()

            # Create all agents
            self._agents = await self.agent_manager.create_all_agents()

            # Create supervisor graph
            self.supervisor_graph = await self._create_supervisor_graph()

            logger.info("SupervisorAgent initialization completed")

        except Exception as e:
            logger.error(f"Failed to initialize SupervisorAgent: {e}")
            raise

    async def _create_supervisor_graph(self) -> Any:
        """Create the supervisor graph with all agents."""
        try:
            # Get agent list for supervisor
            agent_list = list(self._agents.values())

            supervisor = create_supervisor(
                model=self.agent_manager.llm_model,
                agents=agent_list,
                prompt=config.supervisor.prompt,
                add_handoff_back_messages=config.supervisor.add_handoff_back_messages,
                output_mode=config.supervisor.output_mode,
            ).compile()

            logger.info("Supervisor graph created successfully")
            return supervisor

        except Exception as e:
            logger.error(f"Failed to create supervisor graph: {e}")
            raise

    async def process_request(
        self, user_message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process a user request through the supervisor system.

        Args:
            user_message: The user's request message

        Yields:
            Dict containing the processing updates from the supervisor
        """
        if not self.supervisor_graph:
            raise RuntimeError(
                "SupervisorAgent not initialized. Call initialize() first."
            )

        try:
            logger.info(f"Processing user request: {user_message[:100]}...")

            # Create message format for the supervisor
            messages = [{"role": "user", "content": user_message}]

            # Stream the processing through the supervisor
            async for chunk in self.supervisor_graph.astream({"messages": messages}):
                yield chunk

            logger.info("Request processing completed")

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise

    async def process_request_sync(self, user_message: str) -> Dict[str, Any]:
        """Process a user request synchronously and return the final result.

        Args:
            user_message: The user's request message

        Returns:
            Dict containing the final processing result
        """
        final_result = None

        async for chunk in self.process_request(user_message):
            final_result = chunk

        return final_result

    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """Get information about all managed agents.

        Returns:
            Dict containing agent information
        """
        agent_info = {}

        for agent_type, agent_config in config.agents.items():
            agent_info[agent_type] = {
                "name": agent_config.name,
                "description": agent_config.description,
                "status": "active" if agent_type in self._agents else "inactive",
            }

        return agent_info

    def get_system_status(self) -> Dict[str, Any]:
        """Get the current system status.

        Returns:
            Dict containing system status information
        """
        return {
            "supervisor_initialized": self.supervisor_graph is not None,
            "agents_count": len(self._agents),
            "available_agents": list(self._agents.keys()),
            "llm_model": f"{config.llm.provider}:{config.llm.model}",
            "mcp_servers": list(config.mcp_servers.keys()),
        }


class SupervisorService:
    """Service class for managing the supervisor agent lifecycle."""

    def __init__(self):
        """Initialize the supervisor service."""
        self._supervisor: Optional[SupervisorAgent] = None
        self._initialized = False
        logger.info("SupervisorService created")

    async def start(self) -> None:
        """Start the supervisor service."""
        if self._initialized:
            logger.warning("SupervisorService already started")
            return

        try:
            self._supervisor = SupervisorAgent()
            await self._supervisor.initialize()
            self._initialized = True
            logger.info("SupervisorService started successfully")

        except Exception as e:
            logger.error(f"Failed to start SupervisorService: {e}")
            self._supervisor = None
            self._initialized = False
            raise

    async def stop(self) -> None:
        """Stop the supervisor service."""
        if not self._initialized:
            logger.warning("SupervisorService not started")
            return

        try:
            # Cleanup resources if needed
            self._supervisor = None
            self._initialized = False
            logger.info("SupervisorService stopped")

        except Exception as e:
            logger.error(f"Error stopping SupervisorService: {e}")
            raise

    def get_supervisor(self) -> SupervisorAgent:
        """Get the supervisor agent instance.

        Returns:
            The supervisor agent instance

        Raises:
            RuntimeError: If the service is not started
        """
        if not self._initialized or not self._supervisor:
            raise RuntimeError("SupervisorService not started. Call start() first.")

        return self._supervisor

    @property
    def is_running(self) -> bool:
        """Check if the service is running."""
        return self._initialized and self._supervisor is not None


# Global supervisor service instance
supervisor_service = SupervisorService()
