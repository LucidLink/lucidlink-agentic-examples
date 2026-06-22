"""Read a file from a LucidLink filespace and summarize it with Claude (LlamaIndex).

Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY
"""

import os

import lucidlink
from llama_index.llms.anthropic import Anthropic

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs
    brief = fs.read_file("/brief.md").decode()

# Any LlamaIndex LLM works - set the matching provider's API key in your env file.
llm = Anthropic(model="claude-sonnet-4-6", max_tokens=1024)
print(llm.complete(f"Summarize this brief in two sentences:\n\n{brief}"))
