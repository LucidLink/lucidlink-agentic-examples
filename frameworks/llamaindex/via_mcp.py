"""LlamaIndex FunctionAgent using the LucidLink MCP server (tools auto-injected).

`McpToolSpec` turns the MCP server's tools into LlamaIndex tools. We hold one
persistent `ClientSession` for the whole run (not `BasicMCPClient`, which opens
a fresh session per call and loses the linked filespace between tool calls).
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.anthropic import Anthropic
from llama_index.tools.mcp import McpToolSpec
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main() -> None:
    server = StdioServerParameters(
        command="uvx",
        args=["lucidlink-mcp"],
        env={"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
    )
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await McpToolSpec(client=session).to_tool_list_async()

            # max_tokens default is 512; bump it so the base64-encoded write_file
            # payload isn't truncated mid-tool-call.
            agent = FunctionAgent(tools=tools, llm=Anthropic(model="claude-sonnet-4-6", max_tokens=4096))
            response = await agent.run(
                f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
                "and write a one-paragraph summary to /summary.txt."
            )
            print(response)


asyncio.run(main())
