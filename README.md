# LucidLink for AI Agents - Code Samples

Give your AI agents secure, real-time access to the data in your LucidLink filespace. This repository shows
how to connect popular Python agentic frameworks to LucidLink - either through the
[Python SDK](https://pypi.org/project/lucidlink/) (wire filespace `list` / `read` / `write` in as agent
tools) or the [MCP server](https://pypi.org/project/lucidlink-mcp/) (drop in ~35 filespace tools).

## What's here

### Frameworks

Each integration gets its own folder under [`frameworks/`](./frameworks), with tiny, self-contained files -
typically a `via_sdk.py` (hand-wires the SDK as tools) and a `via_mcp.py` (bridges to the MCP server), plus a
`quickstart.py` where it helps.

**→ Browse, set up, and run them from the catalog: [`frameworks/README.md`](./frameworks).**

### IBM Bob mode

A custom **[IBM Bob](https://bob.ibm.com)** mode that lets Bob work with files in your LucidLink
filespace - navigate, preview edits, and edit safely alongside your teammates and other agents.

**→ Set it up: [`ibm_bob_lucidlink_mode/README.md`](./ibm_bob_lucidlink_mode).**

## Links

- [LucidLink Python SDK on PyPI](https://pypi.org/project/lucidlink/)
- [LucidLink MCP server on PyPI](https://pypi.org/project/lucidlink-mcp/)
- [LucidLink Developer Platform KB](https://support.lucidlink.com/hc/en-us/articles/44957651982989-LucidLink-Developer-Platform)
- [LucidLink Support](https://support.lucidlink.com/)
