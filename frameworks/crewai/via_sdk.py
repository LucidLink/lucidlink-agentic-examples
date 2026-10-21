"""CrewAI agent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.workspace
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    filespace = workspace.link_filespace(filespace_id)
    fs = filespace.file_system

    @tool("list_files")
    def list_files(path: str) -> str:
        """List entries in a filespace directory."""
        return "\n".join(e.name for e in fs.read_dir(path))

    @tool("read_file")
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace."""
        return lucidlink.FsUtils(fs).read_bytes(path).decode()

    @tool("write_file")
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace."""
        lucidlink.FsUtils(fs).write_bytes(path, content.encode())
        filespace.sync()
        return f"wrote {path}"

    summarizer = Agent(
        role="Filespace summarizer",
        goal="Summarize briefs stored in a LucidLink filespace",
        backstory="You read and write files in a LucidLink filespace.",
        tools=[list_files, read_file, write_file],
        llm=LLM(model="anthropic/claude-sonnet-5-5"),
    )
    task = Task(
        description="Read /brief.md and write a one-paragraph summary to /summary.txt.",
        expected_output="Confirmation that /summary.txt was written.",
        agent=summarizer,
    )
    print(Crew(agents=[summarizer], tasks=[task]).kickoff())
