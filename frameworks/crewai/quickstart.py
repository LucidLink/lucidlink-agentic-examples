"""Read a file from a LucidLink filespace and summarize it with Claude (CrewAI).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from crewai import LLM

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs
    brief = fs.read_file("/brief.md").decode()

# Any CrewAI LLM string works - set the matching provider's API key in your env file.
llm = LLM(model="anthropic/claude-sonnet-4-6")
print(llm.call(f"Summarize this brief in two sentences:\n\n{brief}"))
