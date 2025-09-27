"""
Supervisor Agent Graph - Main entry point for the multi-agent system.

This module provides a refactored, professional implementation of a supervisor
agent system that manages multiple specialized agents for research, mathematics,
and chart generation tasks.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .exceptions import RequestProcessingError, SupervisorAgentError
from .logging_config import get_logger, setup_logging
from .print_pretty import pretty_print_messages
from .supervisor import supervisor_service

# Setup logging
setup_logging()
logger = get_logger(__name__)


class SupervisorGraph:
    """Main supervisor graph class that manages the multi-agent system."""

    def __init__(self):
        """Initialize the supervisor graph."""
        self._initialized = False
        self.supervisor = None
        logger.info("SupervisorGraph instance created")

    async def initialize(self) -> None:
        """Initialize the supervisor and all agents."""
        if self._initialized:
            logger.warning("SupervisorGraph already initialized")
            return

        try:
            logger.info("Initializing SupervisorGraph...")
            await supervisor_service.start()
            self.supervisor = supervisor_service.get_supervisor()
            self._initialized = True
            logger.info("SupervisorGraph initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SupervisorGraph: {e}")
            raise SupervisorAgentError(f"Initialization failed: {e}")

    async def process_request(self, user_message: str, stream: bool = True) -> Any:
        """Process a user request through the supervisor system.

        Args:
            user_message: The user's request message
            stream: Whether to return streaming results or final result

        Returns:
            Streaming generator if stream=True, final result if stream=False
        """
        if not self._initialized:
            await self.initialize()

        try:
            if stream:
                return self.supervisor.process_request(user_message)
            else:
                return await self.supervisor.process_request_sync(user_message)

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            raise RequestProcessingError(f"Request processing failed: {e}")

    def get_system_info(self) -> Dict[str, Any]:
        """Get information about the system status and agents."""
        if not self._initialized:
            return {"status": "not_initialized"}

        return {
            "status": "initialized",
            "system_status": self.supervisor.get_system_status(),
            "agent_info": self.supervisor.get_agent_info(),
        }


# Global supervisor graph instance
_supervisor_graph: Optional[SupervisorGraph] = None


async def get_supervisor_graph() -> SupervisorGraph:
    """Get or create the global supervisor graph instance.

    Returns:
        The supervisor graph instance
    """
    global _supervisor_graph

    if _supervisor_graph is None:
        _supervisor_graph = SupervisorGraph()
        await _supervisor_graph.initialize()

    return _supervisor_graph


async def create_supervisor_graph() -> SupervisorGraph:
    """Create and initialize a new supervisor graph.

    This function is kept for backward compatibility.

    Returns:
        Initialized supervisor graph instance
    """
    logger.info("Creating supervisor graph (legacy function)")
    return await get_supervisor_graph()


async def process_user_request(user_message: str, stream: bool = True) -> Any:
    """Process a user request through the supervisor system.

    This is a convenience function for processing requests.

    Args:
        user_message: The user's request message
        stream: Whether to return streaming results or final result

    Returns:
        Streaming generator if stream=True, final result if stream=False
    """
    supervisor_graph = await get_supervisor_graph()
    return await supervisor_graph.process_request(user_message, stream)


async def get_system_info() -> Dict[str, Any]:
    """Get information about the system status and agents.

    Returns:
        Dict containing system information
    """
    supervisor_graph = await get_supervisor_graph()
    return supervisor_graph.get_system_info()


# Legacy support - create graph instance for backward compatibility
try:
    graph = asyncio.run(create_supervisor_graph())
    logger.info("Legacy graph instance created successfully")
except Exception as e:
    logger.error(f"Failed to create legacy graph instance: {e}")
    graph = None


async def main():
    """Main function for running the supervisor agent system."""
    try:
        logger.info("Starting supervisor agent system...")

        # Example request
        user_request = (
            "请按以下步骤完成任务：1. 查找2024年北京和上海的GDP数据；"
            "2. 计算上海GDP占中国GDP的比重；3. 为这些数据生成可视化图表"
        )

        logger.info(f"Processing request: {user_request}")

        # Process request with streaming
        async for chunk in await process_user_request(user_request, stream=True):
            # Uncomment the following line to see detailed output
            # pretty_print_messages(chunk, last_message=True)
            pass

        # Get final result
        final_result = chunk
        if "supervisor" in final_result and "messages" in final_result["supervisor"]:
            final_messages = final_result["supervisor"]["messages"]
            logger.info("Request processing completed")
            print("\n=== Final Result ===")
            print(final_messages[-1].content if final_messages else "No final message")

        # Display system information
        system_info = await get_system_info()
        logger.info(f"System status: {system_info}")

    except Exception as e:
        logger.error(f"Error in main function: {e}")
        raise


async def demo():
    """Demo function showing different ways to use the system."""
    try:
        logger.info("Running demo...")

        # Get system info
        info = await get_system_info()
        print("System Information:")
        print(f"Status: {info.get('status')}")
        print(
            f"Available agents: {info.get('system_status', {}).get('available_agents', [])}"
        )

        # Simple request
        simple_request = "查找苹果公司2024年的股价信息"
        print(f"\nProcessing simple request: {simple_request}")

        result = await process_user_request(simple_request, stream=False)
        print("Request completed successfully")

    except Exception as e:
        logger.error(f"Error in demo: {e}")
        raise


# Entry point
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        asyncio.run(demo())
    else:
        asyncio.run(main())
