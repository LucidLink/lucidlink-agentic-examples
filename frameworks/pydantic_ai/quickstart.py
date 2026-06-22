"""Read a file from a LucidLink filespace and summarize it with Claude (Pydantic AI).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from pydantic_ai import Agent

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs
    brief = fs.read_file("/brief.md").decode()

# Any Pydantic AI model string works - set the matching provider's API key in your env file.
result = Agent("anthropic:claude-sonnet-4-6").run_sync(f"Summarize this brief in two sentences:\n\n{brief}")
print(result.output)
