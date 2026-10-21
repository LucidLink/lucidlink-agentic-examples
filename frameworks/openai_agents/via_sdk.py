"""OpenAI Agents SDK agent with LucidLink filespace tools (Python SDK).

This SDK is OpenAI-native, so this example uses an OpenAI model.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, OPENAI_API_KEY
"""

import os

import lucidlink
from agents import Agent, Runner, function_tool

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.workspace
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    filespace = workspace.link_filespace(filespace_id)
    fs = filespace.file_system

    @function_tool
    def list_files(path: str = "/") -> list[str]:
        """List entries in a filespace directory."""
        return [e.name for e in fs.read_dir(path)]

    @function_tool
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace."""
        return lucidlink.FsUtils(fs).read_bytes(path).decode()

    @function_tool
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace."""
        lucidlink.FsUtils(fs).write_bytes(path, content.encode())
        filespace.sync()
        return f"wrote {path}"

    agent = Agent(
        name="Filespace assistant",
        instructions="Use the tools to read and write files in the LucidLink filespace.",
        model="gpt-5.6-luna",
        tools=[list_files, read_file, write_file],
    )
    result = Runner.run_sync(agent, "Read /brief.md and write a one-paragraph summary to /summary.txt.")
    print(result.final_output)
