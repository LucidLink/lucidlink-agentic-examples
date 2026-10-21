"""Read a file from a LucidLink filespace and summarize it with Claude.

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from anthropic import Anthropic

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.workspace
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(filespace_id).file_system
    brief = lucidlink.FsUtils(fs).read_bytes("/brief.md").decode()

message = Anthropic().messages.create(
    model="claude-sonnet-5-5",
    max_tokens=16000,
    messages=[{"role": "user", "content": f"Summarize this brief in two sentences:\n\n{brief}"}],
)
print("".join(b.text for b in message.content if b.type == "text"))
