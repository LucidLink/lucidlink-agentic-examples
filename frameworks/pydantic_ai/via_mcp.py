"""Pydantic AI agent using the LucidLink MCP server (tools auto-injected).

An MCPToolset wraps the stdio server (`uvx lucidlink-mcp`) and exposes its tools.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset, StdioTransport

toolset = MCPToolset(
    StdioTransport(
        command="uvx",
        args=["lucidlink-mcp"],
        env={"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
    )
)
agent = Agent("anthropic:claude-sonnet-4-6", toolsets=[toolset])


async def main() -> None:
    async with agent:
        result = await agent.run(
            f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
            "and write a one-paragraph summary to /summary.txt."
        )
        print(result.output)


asyncio.run(main())
