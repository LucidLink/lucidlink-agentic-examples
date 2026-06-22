"""LangChain / LangGraph agent using the LucidLink MCP server (tools auto-injected).

`langchain-mcp-adapters` launches `uvx lucidlink-mcp` and exposes its tools as
LangChain tools - no hand-wiring.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools


async def main() -> None:
    client = MultiServerMCPClient(
        {
            "lucidlink": {
                "transport": "stdio",
                "command": "uvx",
                "args": ["lucidlink-mcp"],
                "env": {"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
            }
        }
    )
    async with client.session("lucidlink") as session:
        tools = await load_mcp_tools(session)

        agent = create_agent(init_chat_model("anthropic:claude-sonnet-4-6"), tools)
        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
                        "and write a one-paragraph summary to /summary.txt.",
                    }
                ]
            }
        )
        print(result["messages"][-1].content)


asyncio.run(main())
