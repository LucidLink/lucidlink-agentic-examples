# Wire a terminal AI agent to the LucidLink MCP

## OpenClaw

```bash
# 1. MCP server
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install lucidlink-mcp
lucidlink-mcp-setup                                  # paste your sa_live:... token

# 2. OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash     # onboard: pick a model provider + model
openclaw mcp add lucidlink --command "$(command -v lucidlink-mcp)"
openclaw mcp probe lucidlink                         # connects, no LLM call

# 3. Chat
openclaw chat
#   > create /mcp-smoke.txt with "hello from OpenClaw", then read it back
```

## Hermes

```bash
# 1. MCP server
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install lucidlink-mcp
lucidlink-mcp-setup                                  # paste your sa_live:... token

# 2. Hermes (self-contained runtime)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes mcp add lucidlink --command "$(command -v lucidlink-mcp)"   # answer Y to "enable all tools?"
hermes mcp test lucidlink                            # connects, no LLM call
hermes model                                         # pick a model provider + model

# 3. Chat
hermes
#   > create /mcp-smoke.txt with "hello from Hermes", then read it back
```

## NemoClaw

The daemon cannot run in the sandbox: OpenShell egress is proxy-only and the daemon does its own DNS, so it cannot traverse the CONNECT proxy (upstream: [NVIDIA/OpenShell#1107](https://github.com/NVIDIA/OpenShell/issues/1107)). Run the MCP on the host and reach it over SSE. `<sb>` is your sandbox name.

```bash
# 1. HOST: MCP server + token, served over SSE on the sandbox's bridge gateway IP
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv tool install lucidlink-mcp
lucidlink-mcp-setup                                  # paste your sa_live:... token
CID=$(docker ps --format '{{.Names}}' | grep -m1 "openshell-<sb>-")
BRIDGE=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}' "$CID")
LUCIDLINK_FILESPACE=<your-filespace> uvx mcp-proxy --host "$BRIDGE" --port 8808 --pass-environment lucidlink-mcp &

# 2. SANDBOX: allow the agent's node binary to reach that endpoint
cat > lucidlink-sse.yaml <<YAML
preset: { name: lucidlink-sse, description: "host LucidLink MCP over SSE" }
network_policies:
  lucidlink-sse:
    name: lucidlink-sse
    endpoints:
      - { host: "$BRIDGE", port: 8808, access: full, tls: skip, allowed_ips: ["$BRIDGE/32"] }
    binaries:
      - { path: /usr/local/bin/node }
YAML
nemoclaw <sb> policy-add --from-file lucidlink-sse.yaml --yes

# 3. Chat
nemoclaw <sb> exec -- openclaw mcp set lucidlink "{\"type\":\"sse\",\"url\":\"http://$BRIDGE:8808/sse\"}"
nemoclaw <sb> exec -- openclaw agent --agent main -m "create /mcp-smoke.txt with 'hello from NemoClaw', then read it back"
```
