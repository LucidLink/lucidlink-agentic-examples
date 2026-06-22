"""Pydantic AI agent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from pydantic_ai import Agent

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs

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
