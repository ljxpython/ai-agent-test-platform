from __future__ import annotations

import asyncio
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient


async def aget_mcp_server_chart_tools() -> list[Any]:
    client = MultiServerMCPClient(
        {
            "mcp_chart_server": {
                "command": "npx",
                "args": ["-y", "@antv/mcp-server-chart"],
                "transport": "stdio",
            }
        }
    )
    return await client.get_tools()


def get_mcp_server_chart_tools() -> list[Any]:
    return asyncio.run(aget_mcp_server_chart_tools())
