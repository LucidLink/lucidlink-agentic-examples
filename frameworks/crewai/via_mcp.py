"""CrewAI agent using the LucidLink MCP server.

`crewai-tools` (MCPServerAdapter) launches `uvx lucidlink-mcp` and adapts its
tools into CrewAI tools.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

from crewai import LLM, Agent, Crew, Task
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters

# CrewAI marks every tool `strict`, and Anthropic caps strict tools at 20 while
# lucidlink-mcp exposes ~40. Scope to the handful this task needs - good practice
# anyway, since a focused toolset makes the agent pick the right tool reliably.
TOOLS = {"link_filespace", "read_file", "write_file", "list_files"}

server = StdioServerParameters(
    command="uvx",
    args=["lucidlink-mcp"],
    env={"LUCIDLINK_TOKEN": os.environ["LUCIDLINK_TOKEN"]},
)

with MCPServerAdapter(server) as mcp_tools:
    agent = Agent(
        role="Filespace summarizer",
        goal="Summarize briefs stored in a LucidLink filespace",
        backstory="You manage files in a LucidLink filespace via MCP tools.",
        tools=[t for t in mcp_tools if t.name in TOOLS],
        llm=LLM(model="anthropic/claude-sonnet-4-6"),
    )
    task = Task(
        description=(
            f"Link the filespace '{os.environ['LUCIDLINK_FILESPACE']}', read /brief.md, "
            "and write a one-paragraph summary to /summary.txt."
        ),
        expected_output="Confirmation that /summary.txt was written.",
        agent=agent,
    )
    print(Crew(agents=[agent], tasks=[task]).kickoff())
