"""Smolagents CodeAgent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from smolagents import CodeAgent, LiteLLMModel, tool

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.workspace
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    filespace = workspace.link_filespace(filespace_id)
    fs = filespace.file_system

    @tool
    def list_files(path: str) -> list:
        """List entries in a filespace directory.

        Args:
            path: Directory path in the filespace, e.g. "/".
        """
        return [e.name for e in fs.read_dir(path)]

    @tool
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace.

        Args:
            path: File path, e.g. "/brief.md".
        """
        return lucidlink.FsUtils(fs).read_bytes(path).decode()

    @tool
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace.

        Args:
            path: Destination path, e.g. "/summary.txt".
            content: Text to write.
        """
        lucidlink.FsUtils(fs).write_bytes(path, content.encode())
        filespace.sync()
        return f"wrote {path}"

    agent = CodeAgent(
        tools=[list_files, read_file, write_file],
        # LiteLLMModel is a wrapper allowing the use of any model, we can decide which one to use for
        # the examples
        model=LiteLLMModel("anthropic/claude-sonnet-5-5"),
    )
    print(agent.run("Read /brief.md and write a one-paragraph summary to /summary.txt."))
