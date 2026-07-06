"""Read a file from a LucidLink filespace and summarize it with Claude (Smolagents).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from smolagents import LiteLLMModel

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.get_workspace(client.list_workspaces()[0].id)
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(id=filespace_id).fs
    brief = fs.read_file("/brief.md").decode()

# LiteLLMModel wraps any provider - set the matching provider's API key in your env file.
model = LiteLLMModel("anthropic/claude-sonnet-4-6")
messages = [{"role": "user", "content": f"Summarize this brief in two sentences:\n\n{brief}"}]
print(model(messages).content)
