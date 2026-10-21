"""Pydantic AI agent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from pydantic_ai import Agent

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.workspace
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    filespace = workspace.link_filespace(filespace_id)
    fs = filespace.file_system

    agent = Agent("anthropic:claude-sonnet-5-5")

    @agent.tool_plain
    def list_files(path: str = "/") -> list[str]:
        """List entries in a filespace directory."""
        return [e.name for e in fs.read_dir(path)]

    @agent.tool_plain
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace."""
        return lucidlink.FsUtils(fs).read_bytes(path).decode()

    @agent.tool_plain
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace."""
        lucidlink.FsUtils(fs).write_bytes(path, content.encode())
        filespace.sync()
        return f"wrote {path}"

    result = agent.run_sync("Read /brief.md and write a one-paragraph summary to /summary.txt.")
    print(result.output)
