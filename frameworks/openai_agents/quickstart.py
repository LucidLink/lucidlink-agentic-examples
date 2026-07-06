"""Read a file from a LucidLink filespace and summarize it with an LLM (OpenAI Agents SDK).

This SDK is OpenAI-native, so this example uses an OpenAI model.
Env: LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE, OPENAI_API_KEY
"""

import os

import lucidlink
from agents import Agent, Runner

with lucidlink.Client() as client:
    client.login(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    workspace = client.get_workspace(client.list_workspaces()[0].id)
    filespace_id = next(f.id for f in workspace.list_filespaces() if f.name == os.environ["LUCIDLINK_FILESPACE"])
    fs = workspace.link_filespace(id=filespace_id).fs
    brief = fs.read_file("/brief.md").decode()

agent = Agent(name="Summarizer", instructions="Summarize briefs concisely.", model="gpt-4o-mini")
result = Runner.run_sync(agent, f"Summarize this brief in two sentences:\n\n{brief}")
print(result.final_output)
