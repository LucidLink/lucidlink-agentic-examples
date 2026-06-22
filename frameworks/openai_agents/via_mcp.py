"""OpenAI Agents SDK agent using the LucidLink MCP server (tools auto-injected).

The SDK launches `uvx lucidlink-mcp` and exposes its tools natively.
This SDK is OpenAI-native, so this example uses an OpenAI model.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, OPENAI_API_KEY
"""

import asyncio
import os

from agents import Agent, Runner
from agents.mcp import MCPServerStdio


async def main() -> None:
    # First call may be slow while uvx fetches the server - allow extra time.
    async with MCPServerStdio(
        params={
            "command": "uvx",
            "args": ["lucidlink-mcp"],
            "env": {"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
        },
        client_session_timeout_seconds=60,
    ) as server:
        agent = Agent(
            name="Filespace assistant",
            instructions="Use the LucidLink tools to manage filespace files.",
            model="gpt-4o-mini",
            mcp_servers=[server],
        )
        result = await Runner.run(
            agent,
            f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
            "and write a one-paragraph summary to /summary.txt.",
        )
        print(result.final_output)


asyncio.run(main())
