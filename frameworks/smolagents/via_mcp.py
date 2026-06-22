"""Smolagents CodeAgent using the LucidLink MCP server (tools auto-injected).

`ToolCollection.from_mcp` launches `uvx lucidlink-mcp` and exposes its tools.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

from mcp import StdioServerParameters
from smolagents import CodeAgent, LiteLLMModel, ToolCollection

server = StdioServerParameters(
    command="uvx",
    args=["lucidlink-mcp"],
    env={"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
)

with ToolCollection.from_mcp(server, trust_remote_code=True) as tools:
    agent = CodeAgent(tools=[*tools.tools], model=LiteLLMModel("anthropic/claude-sonnet-4-6"))
    print(
        agent.run(
            f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
            "and write a one-paragraph summary to /summary.txt."
        )
    )
