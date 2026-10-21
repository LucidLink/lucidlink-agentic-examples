"""Read a file from a LucidLink filespace and summarize it with Claude (LangChain).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from langchain.chat_models import init_chat_model

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.workspace
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(filespace_id).file_system
    brief = lucidlink.FsUtils(fs).read_bytes("/brief.md").decode()

# Any LangChain model string works - set the matching provider's API key in your env file.
model = init_chat_model("anthropic:claude-sonnet-5-5")
print(model.invoke(f"Summarize this brief in two sentences:\n\n{brief}").text)
