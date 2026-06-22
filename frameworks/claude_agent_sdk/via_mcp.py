"""Claude Agent SDK (the Claude Code engine, as a library) using the LucidLink MCP server.

Unlike `claude_mcp.py` (Anthropic SDK - you drive the loop), the Agent SDK runs the
agentic loop for you: declare the stdio server under `mcp_servers`, allow its tools,
and hand it the task. `allowed_tools` is scoped to `mcp__lucidlink__*` so the agent
uses only the filespace tools, not the Agent SDK's built-in local file/bash tools.
Requires the Claude Code CLI on PATH.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


async def main() -> None:
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        mcp_servers={
            "lucidlink": {
                "command": "uvx",
                "args": ["lucidlink-mcp"],
                "env": {"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
            }
        },
        allowed_tools=["mcp__lucidlink__*"],
    )
    prompt = (
        f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
        "and write a one-paragraph summary to /summary.txt."
    )
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)


asyncio.run(main())
