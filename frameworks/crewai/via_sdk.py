"""CrewAI agent with LucidLink filespace tools (Python SDK).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from crewai import LLM, Agent, Crew, Task
from crewai.tools import tool

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.get_workspace(client.list_workspaces()[0].id)
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(id=filespace_id).fs

    @tool("list_files")
    def list_files(path: str) -> str:
        """List entries in a filespace directory."""
        return "\n".join(e.name for e in fs.read_dir(path))

    @tool("read_file")
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the filespace."""
        return fs.read_file(path).decode()

    @tool("write_file")
    def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file to the filespace."""
        fs.write_file(path, content.encode())
        return f"wrote {path}"

    summarizer = Agent(
        role="Filespace summarizer",
        goal="Summarize briefs stored in a LucidLink filespace",
        backstory="You read and write files in a LucidLink filespace.",
        tools=[list_files, read_file, write_file],
        llm=LLM(model="anthropic/claude-sonnet-4-6"),
    )
    task = Task(
        description="Read /brief.md and write a one-paragraph summary to /summary.txt.",
        expected_output="Confirmation that /summary.txt was written.",
        agent=summarizer,
    )
    print(Crew(agents=[summarizer], tasks=[task]).kickoff())
