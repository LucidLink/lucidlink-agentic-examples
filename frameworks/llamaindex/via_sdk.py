"""LlamaIndex FunctionAgent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import asyncio
import os

import lucidlink
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.anthropic import Anthropic


async def main() -> None:
    with lucidlink.Client() as client:
        client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
        workspace = client.workspace
        filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
        filespace = workspace.link_filespace(filespace_id)
        fs = filespace.file_system

        def list_files(path: str = "/") -> list[str]:
            """List entries in a filespace directory."""
            return [e.name for e in fs.read_dir(path)]

        def read_file(path: str) -> str:
            """Read a UTF-8 text file from the filespace."""
            return lucidlink.FsUtils(fs).read_bytes(path).decode()

        def write_file(path: str, content: str) -> str:
            """Write a UTF-8 text file to the filespace."""
            lucidlink.FsUtils(fs).write_bytes(path, content.encode())
            filespace.sync()
            return f"wrote {path}"

        agent = FunctionAgent(
            tools=[list_files, read_file, write_file],
            llm=Anthropic(model="claude-sonnet-5-5", max_tokens=4096),  # default is 512
        )
        response = await agent.run("Read /brief.md and write a one-paragraph summary to /summary.txt.")
        print(response)


asyncio.run(main())
