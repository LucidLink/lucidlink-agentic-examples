"""Claude (Anthropic SDK) using the LucidLink MCP server (tools auto-injected).

`anthropic[mcp]` converts the MCP server's tools with `async_mcp_tool` and runs
them through `tool_runner`. (The Claude Agent SDK's `ClaudeAgentOptions(mcp_servers=...)`
is an alternative way to wire the same server.)
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

import anthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command="uvx",
        args=["lucidlink-mcp"],
        env={"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as mcp:
            await mcp.initialize()
            tools = await mcp.list_tools()

            runner = anthropic.AsyncAnthropic().beta.messages.tool_runner(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
                        "and write a one-paragraph summary to /summary.txt.",
                    }
                ],
                tools=[async_mcp_tool(t, mcp) for t in tools.tools],
            )
            final = None
            async for message in runner:
                final = message
            print("".join(b.text for b in final.content if b.type == "text"))


asyncio.run(main())
