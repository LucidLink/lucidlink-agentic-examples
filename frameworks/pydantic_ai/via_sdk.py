"""Pydantic AI agent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from pydantic_ai import Agent

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.get_workspace(client.list_workspaces()[0].id)
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(id=filespace_id).fs

    agent = Agent("anthropic:claude-sonnet-4-6")

    @agent.tool_plain
    def list_files(path: str = "/") -> list[str]:
        """List entries in a filespace directory."""
        return [e.name for e in fs.read_dir(path)]

    @agent.tool_plain
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace."""
        return fs.read_file(path).decode()

    @agent.tool_plain
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace."""
        fs.write_file(path, content.encode())
        return f"wrote {path}"

    result = agent.run_sync("Read /brief.md and write a one-paragraph summary to /summary.txt.")
    print(result.output)
