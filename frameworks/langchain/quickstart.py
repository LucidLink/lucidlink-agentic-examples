"""Read a file from a LucidLink filespace and summarize it with Claude (LangChain).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from langchain.chat_models import init_chat_model

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs
    brief = fs.read_file("/brief.md").decode()

# Any LangChain model string works - set the matching provider's API key in your env file.
model = init_chat_model("anthropic:claude-sonnet-4-6")
print(model.invoke(f"Summarize this brief in two sentences:\n\n{brief}").content)
