"""Read a file from a LucidLink filespace and summarize it with Claude (Claude Agent SDK).

Requires the Claude Code CLI on PATH.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

import lucidlink
from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


async def main() -> None:
    with lucidlink.Client() as client:
        client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
        workspace = client.get_workspace(client.list_workspaces()[0].id)
        filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
        fs = workspace.link_filespace(id=filespace_id).fs
        brief = fs.read_file("/brief.md").decode()

    async for message in query(
        prompt=f"Summarize this brief in two sentences:\n\n{brief}",
        options=ClaudeAgentOptions(model="claude-sonnet-4-6", tools=[]),
    ):
        if isinstance(message, ResultMessage) and message.subtype == "success":
            print(message.result)


asyncio.run(main())
