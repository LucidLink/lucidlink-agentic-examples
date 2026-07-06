"""Claude Agent SDK with LucidLink tools wired in-process via the Python SDK (no MCP server).

`@tool` defines in-process tools backed by the LucidLink Python SDK; `create_sdk_mcp_server`
bundles them so the Agent SDK runs its loop against your own functions - no `uvx lucidlink-mcp`
subprocess. Contrast `via_mcp.py`, which bridges to the MCP server instead.
Requires the Claude Code CLI on PATH.
Env: LUCIDLINK_TOKEN (service-account token, sa_live:...), LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

import lucidlink
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ResultMessage,
    create_sdk_mcp_server,
    query,
    tool,
)


async def main() -> None:
    with lucidlink.Client() as client:
        client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
        workspace = client.get_workspace(client.list_workspaces()[0].id)
        filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
        fs = workspace.link_filespace(id=filespace_id).fs

        @tool("list_files", "List entries in a filespace directory.", {"path": str})
        async def list_files(args: dict) -> dict:
            names = "\n".join(e.name for e in fs.read_dir(args["path"]))
            return {"content": [{"type": "text", "text": names}]}

        @tool("read_file", "Read a UTF-8 text file from the filespace.", {"path": str})
        async def read_file(args: dict) -> dict:
            return {"content": [{"type": "text", "text": fs.read_file(args["path"]).decode()}]}

        @tool("write_file", "Write a UTF-8 text file to the filespace.", {"path": str, "content": str})
        async def write_file(args: dict) -> dict:
            fs.write_file(args["path"], args["content"].encode())
            return {"content": [{"type": "text", "text": f"wrote {args['path']}"}]}

        server = create_sdk_mcp_server(
            name="lucidlink",
            version="1.0.0",
            tools=[list_files, read_file, write_file],
        )
        options = ClaudeAgentOptions(
            model="claude-sonnet-4-6",
            tools=[],  # drop built-in file/bash tools - agent uses only our filespace tools
            mcp_servers={"lucidlink": server},
            allowed_tools=["mcp__lucidlink__*"],
        )
        async for message in query(
            prompt="Read /brief.md and write a one-paragraph summary to /summary.txt.",
            options=options,
        ):
            if isinstance(message, ResultMessage) and message.subtype == "success":
                print(message.result)


asyncio.run(main())
