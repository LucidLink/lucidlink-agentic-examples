"""Read a file from a LucidLink filespace and summarize it with Claude (Pydantic AI).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from pydantic_ai import Agent

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.get_workspace(client.list_workspaces()[0].id)
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(id=filespace_id).fs
    brief = fs.read_file("/brief.md").decode()

# Any Pydantic AI model string works - set the matching provider's API key in your env file.
result = Agent("anthropic:claude-sonnet-4-6").run_sync(f"Summarize this brief in two sentences:\n\n{brief}")
print(result.output)
