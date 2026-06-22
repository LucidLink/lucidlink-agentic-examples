"""Read a file from a LucidLink filespace and summarize it with Claude.

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from anthropic import Anthropic

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs
    brief = fs.read_file("/brief.md").decode()

message = Anthropic().messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": f"Summarize this brief in two sentences:\n\n{brief}"}],
)
print(message.content[0].text)
