"""
Usage examples for the Supervisor Agent System.

This module provides various examples of how to use the supervisor agent system
for different types of tasks and scenarios.
"""

import asyncio
import logging
from typing import Any, Dict

from . import (
    SupervisorGraph,
    get_logger,
    get_system_info,
    process_user_request,
    supervisor_service,
)

logger = get_logger(__name__)


async def example_basic_usage():
    """Example of basic usage with the convenience function."""
    print("=== Basic Usage Example ===")

    try:
        # Simple request processing
        request = "查找苹果公司2024年的最新股价信息"
        print(f"Request: {request}")

        # Process with streaming (default)
        print("\nProcessing with streaming...")
        async for chunk in await process_user_request(request):
            # In a real application, you might want to process each chunk
            pass

        print("✅ Basic usage completed successfully")

    except Exception as e:
        print(f"❌ Error in basic usage: {e}")
        logger.error(f"Basic usage error: {e}")


async def example_advanced_usage():
    """Example of advanced usage with direct SupervisorGraph control."""
    print("\n=== Advanced Usage Example ===")

    try:
        # Create and initialize supervisor graph
        supervisor = SupervisorGraph()
        await supervisor.initialize()

        # Complex multi-step request
        request = (
            "请完成以下任务：1. 查找中国2024年第三季度GDP数据；"
            "2. 计算与去年同期的增长率；3. 创建一个显示增长趋势的图表"
        )
        print(f"Request: {request}")

        # Process with detailed control
        print("\nProcessing with detailed control...")
        chunk_count = 0
        async for chunk in await supervisor.process_request(request):
            chunk_count += 1
            print(f"Received chunk {chunk_count}")
            # Process each chunk as needed

        # Get system information
        system_info = supervisor.get_system_info()
        print(f"\nSystem Info: {system_info}")

        print("✅ Advanced usage completed successfully")

    except Exception as e:
        print(f"❌ Error in advanced usage: {e}")
        logger.error(f"Advanced usage error: {e}")


async def example_service_management():
    """Example of service lifecycle management."""
    print("\n=== Service Management Example ===")

    try:
        # Check service status
        print(f"Service running: {supervisor_service.is_running}")

        # Start service if not running
        if not supervisor_service.is_running:
            print("Starting supervisor service...")
            await supervisor_service.start()

        # Get supervisor instance
        supervisor = supervisor_service.get_supervisor()

        # Use the supervisor
        request = "查找特斯拉公司的最新财务报告"
        print(f"Processing: {request}")

        result = await supervisor.process_request_sync(request)
        print("✅ Request processed successfully")

        # Get agent information
        agent_info = supervisor.get_agent_info()
        print(f"Available agents: {list(agent_info.keys())}")

        print("✅ Service management completed successfully")

    except Exception as e:
        print(f"❌ Error in service management: {e}")
        logger.error(f"Service management error: {e}")


async def example_error_handling():
    """Example of proper error handling."""
    print("\n=== Error Handling Example ===")

    try:
        # Test with potentially problematic request
        request = "执行一个可能失败的复杂任务"
        print(f"Request: {request}")

        try:
            result = await process_user_request(request, stream=False)
            print("✅ Request completed without errors")

        except Exception as request_error:
            print(f"⚠️ Request failed as expected: {request_error}")
            logger.warning(f"Expected request failure: {request_error}")

        # Test system recovery
        print("\nTesting system recovery...")
        simple_request = "查找今天的天气信息"
        result = await process_user_request(simple_request, stream=False)
        print("✅ System recovered successfully")

        print("✅ Error handling example completed")

    except Exception as e:
        print(f"❌ Unexpected error in error handling: {e}")
        logger.error(f"Error handling example error: {e}")


async def example_system_monitoring():
    """Example of system monitoring and status checking."""
    print("\n=== System Monitoring Example ===")

    try:
        # Get comprehensive system information
        system_info = await get_system_info()

        print("System Status:")
        print(f"  Status: {system_info.get('status')}")

        if system_info.get("system_status"):
            status = system_info["system_status"]
            print(f"  Supervisor Initialized: {status.get('supervisor_initialized')}")
            print(f"  Agents Count: {status.get('agents_count')}")
            print(f"  Available Agents: {status.get('available_agents')}")
            print(f"  LLM Model: {status.get('llm_model')}")
            print(f"  MCP Servers: {status.get('mcp_servers')}")

        if system_info.get("agent_info"):
            print("\nAgent Information:")
            for agent_name, info in system_info["agent_info"].items():
                print(f"  {agent_name}:")
                print(f"    Name: {info.get('name')}")
                print(f"    Description: {info.get('description')}")
                print(f"    Status: {info.get('status')}")

        print("✅ System monitoring completed successfully")

    except Exception as e:
        print(f"❌ Error in system monitoring: {e}")
        logger.error(f"System monitoring error: {e}")


async def run_all_examples():
    """Run all examples in sequence."""
    print("🚀 Running Supervisor Agent System Examples")
    print("=" * 50)

    examples = [
        example_basic_usage,
        example_advanced_usage,
        example_service_management,
        example_error_handling,
        example_system_monitoring,
    ]

    for i, example_func in enumerate(examples, 1):
        try:
            print(f"\n[{i}/{len(examples)}] Running {example_func.__name__}")
            await example_func()

        except Exception as e:
            print(f"❌ Example {example_func.__name__} failed: {e}")
            logger.error(f"Example {example_func.__name__} failed: {e}")

        # Small delay between examples
        await asyncio.sleep(1)

    print("\n" + "=" * 50)
    print("🎉 All examples completed!")


async def interactive_demo():
    """Interactive demo that allows user input."""
    print("\n=== Interactive Demo ===")
    print("Enter your requests (type 'quit' to exit, 'help' for examples)")

    try:
        while True:
            user_input = input("\n> ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if user_input.lower() == "help":
                print("\nExample requests:")
                print("- 查找苹果公司的最新股价")
                print("- 计算100除以3的结果")
                print("- 为销售数据创建一个柱状图")
                print("- 查找2024年中国GDP数据并计算增长率")
                continue

            if not user_input:
                continue

            print(f"Processing: {user_input}")

            try:
                # Process the request
                result = await process_user_request(user_input, stream=False)
                print("✅ Request completed successfully")

            except Exception as e:
                print(f"❌ Error processing request: {e}")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"❌ Error in interactive demo: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "interactive":
            asyncio.run(interactive_demo())
        elif sys.argv[1] == "basic":
            asyncio.run(example_basic_usage())
        elif sys.argv[1] == "advanced":
            asyncio.run(example_advanced_usage())
        elif sys.argv[1] == "service":
            asyncio.run(example_service_management())
        elif sys.argv[1] == "error":
            asyncio.run(example_error_handling())
        elif sys.argv[1] == "monitor":
            asyncio.run(example_system_monitoring())
        else:
            print(
                "Available options: interactive, basic, advanced, service, error, monitor"
            )
    else:
        asyncio.run(run_all_examples())
