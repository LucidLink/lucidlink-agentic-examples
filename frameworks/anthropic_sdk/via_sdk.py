"""Claude (Anthropic SDK) tool-runner with LucidLink filespace tools (Python SDK).

`@beta_tool` turns plain functions into tools; `tool_runner` drives the agentic
loop until Claude is done.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import anthropic
import lucidlink
from anthropic import beta_tool

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs

    @beta_tool
    def list_files(path: str) -> str:
        """List entries in a filespace directory.

        Args:
            path: Directory path, e.g. "/".
        """
        return "\n".join(e.name for e in fs.read_dir(path))

    @beta_tool
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace.

        Args:
            path: File path, e.g. "/brief.md".
        """
        return fs.read_file(path).decode()

    @beta_tool
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace.

        Args:
            path: Destination path, e.g. "/summary.txt".
            content: Text to write.
        """
        fs.write_file(path, content.encode())
        return f"wrote {path}"

    runner = anthropic.Anthropic().beta.messages.tool_runner(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        tools=[list_files, read_file, write_file],
        messages=[{"role": "user", "content": "Read /brief.md and write a one-paragraph summary to /summary.txt."}],
    )
    final = None
    for message in runner:
        final = message
    print("".join(b.text for b in final.content if b.type == "text"))
