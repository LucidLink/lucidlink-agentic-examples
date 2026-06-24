# Frameworks - snippet catalog

One folder per framework. Each holds up to three tiny, self-contained files showing the essence of
"LucidLink + this framework":

- **`quickstart.py`** - the smallest possible read: authenticate, read `/brief.md`, summarize it.
- **`via_sdk.py`** - hand-wire the LucidLink **Python SDK** (`list` / `read` / `write`) as the framework's
  own tools.
- **`via_mcp.py`** - point the framework at the **LucidLink MCP server** (`uvx lucidlink-mcp`) via its MCP
  bridge; ~35 filespace tools get injected with almost no glue.

The `via_sdk.py` / `via_mcp.py` files run the **same task** - *read `/brief.md`, write a one-paragraph summary
to `/summary.txt`* - so you can compare the two wiring styles across frameworks side by side.

Claude appears via **two Anthropic SDKs**, in their own folders: the **Anthropic SDK**
([`anthropic_sdk/`](./anthropic_sdk)) is the model client where you drive the loop yourself; the
**Claude Agent SDK** ([`claude_agent_sdk/`](./claude_agent_sdk)) is the Claude Code engine as a library,
which runs the loop for you. One quirk: for the Agent SDK even the *SDK*-track tools are registered through
an in-process MCP server (`create_sdk_mcp_server`) - its tool model is always MCP.

## Prerequisites

- **Python ≥ 3.10** and **[uv](https://docs.astral.sh/uv/)**
  (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- A **LucidLink service-account token** (`sa_live:...`) and a **filespace name**.
  [Service accounts →](https://support.lucidlink.com/hc/en-us/articles/40222074543757-Getting-Started-with-Service-Accounts-API-Authentication)
- An **`ANTHROPIC_API_KEY`** (snippets default to Anthropic models).

## Seed the filespace

These snippets all read `/brief.md`. Write a demo one - or drop in your own markdown at that path:

```bash
cp .env.example .env          # fill in LUCIDLINK_TOKEN + LUCIDLINK_FILESPACE
set -a; source .env; set +a
uv run --with lucidlink seed.py
```

## Models

Snippets default to Anthropic models. To use another provider, change the model string (or
provider-specific constructor) in the file and add that provider's API key to your env file.

## Track caveats

- `via_mcp.py` snippets launch the LucidLink MCP server as a subprocess via `uvx lucidlink-mcp` (uv fetches
  [`lucidlink-mcp`](https://pypi.org/project/lucidlink-mcp/) on first run - no separate install needed).
- The `claude_agent_sdk` snippets additionally need the **Claude Code CLI** on your PATH - the Claude
  Agent SDK runs it under the hood (`npm install -g @anthropic-ai/claude-code`).

## Run a snippet

There's no repo-wide dependency manifest - each snippet lists only the packages it actually needs, so you
install just those instead of every framework's stack. Pass them to `uv run` with `--with` (from the table
below), or `pip install` them and use `python`. Run from this `frameworks/` folder:

```bash
uv run --with lucidlink --with pydantic-ai pydantic_ai/via_sdk.py
```

## Snippets

| Snippet | Framework | Track | LLM | `uv run --with ...` deps |
|---|---|---|---|---|
| `anthropic_sdk/quickstart.py` | Claude (Anthropic SDK) | quickstart | Claude | `lucidlink anthropic` |
| `anthropic_sdk/via_sdk.py` | Claude (Anthropic SDK) | SDK | Claude | `lucidlink anthropic` |
| `anthropic_sdk/via_mcp.py` | Claude (Anthropic SDK) | MCP | Claude | `"anthropic[mcp]"` |
| `claude_agent_sdk/quickstart.py` | Claude Agent SDK | quickstart | Claude | `lucidlink claude-agent-sdk` (+ Claude Code CLI) |
| `claude_agent_sdk/via_sdk.py` | Claude Agent SDK | SDK | Claude | `lucidlink claude-agent-sdk` (+ Claude Code CLI) |
| `claude_agent_sdk/via_mcp.py` | Claude Agent SDK | MCP | Claude | `claude-agent-sdk` (+ Claude Code CLI) |
| `langchain/quickstart.py` | LangChain | quickstart | Claude | `lucidlink langchain langchain-anthropic` |
| `langchain/via_sdk.py` | LangChain / LangGraph | SDK | Claude | `lucidlink langchain langchain-anthropic langgraph` |
| `langchain/via_mcp.py` | LangChain / LangGraph | MCP | Claude | `langchain langchain-anthropic langgraph langchain-mcp-adapters` |
| `llamaindex/quickstart.py` | LlamaIndex | quickstart | Claude | `lucidlink llama-index llama-index-llms-anthropic` |
| `llamaindex/via_sdk.py` | LlamaIndex | SDK | Claude | `lucidlink llama-index llama-index-llms-anthropic` |
| `llamaindex/via_mcp.py` | LlamaIndex | MCP | Claude | `llama-index llama-index-llms-anthropic llama-index-tools-mcp` |
| `pydantic_ai/quickstart.py` | Pydantic AI | quickstart | Claude | `lucidlink pydantic-ai` |
| `pydantic_ai/via_sdk.py` | Pydantic AI | SDK | Claude | `lucidlink pydantic-ai` |
| `pydantic_ai/via_mcp.py` | Pydantic AI | MCP | Claude | `pydantic-ai` |
| `crewai/quickstart.py` | CrewAI | quickstart | Claude | `lucidlink "crewai[anthropic]"` |
| `crewai/via_sdk.py` | CrewAI | SDK | Claude | `lucidlink "crewai[anthropic]"` |
| `crewai/via_mcp.py` | CrewAI | MCP | Claude | `"crewai[anthropic]" "crewai-tools[mcp]"` |
| `openai_agents/quickstart.py` | OpenAI Agents SDK | quickstart | OpenAI | `lucidlink openai-agents` |
| `openai_agents/via_sdk.py` | OpenAI Agents SDK | SDK | OpenAI | `lucidlink openai-agents` |
| `openai_agents/via_mcp.py` | OpenAI Agents SDK | MCP | OpenAI | `openai-agents` |
| `smolagents/quickstart.py` | Smolagents | quickstart | Claude | `lucidlink "smolagents[litellm]"` |
| `smolagents/via_sdk.py` | Smolagents | SDK | Claude | `lucidlink "smolagents[litellm]"` |
| `smolagents/via_mcp.py` | Smolagents | MCP | Claude | `"smolagents[litellm,mcp]"` |
