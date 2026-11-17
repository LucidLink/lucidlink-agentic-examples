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

## NemoClaw (current release)

NemoClaw adds MCP servers as HTTPS endpoints and injects the bearer token at egress, so LucidLink credentials
and decrypted files never enter the sandbox. `<sb>` is your sandbox name.

```bash
# 1. HOST: MCP server behind HTTPS on the host's private address
curl -LsSf https://astral.sh/uv/install.sh | sh && chmod 755 ~/.local
export PATH="$HOME/.local/bin:$PATH"
uv tool install lucidlink-mcp
lucidlink-mcp-setup                                  # paste your sa_live:... token
IP=$(hostname -I | awk '{print $1}')
export LUCIDLINK_MCP_HTTP_BEARER=$(openssl rand -hex 32)
LUCIDLINK_FILESPACE=<your-filespace> lucidlink-mcp --http --no-path-secret --write --port 8811 --allowed-host "$IP" &
caddy reverse-proxy --from "https://$IP:8443" --to 127.0.0.1:8811 --internal-certs --disable-redirects &   # needs Caddy installed

# 2. SANDBOX: trust Caddy's certificate
NEMOCLAW_CORPORATE_CA_BUNDLE=~/.local/share/caddy/pki/authorities/local/root.crt nemoclaw onboard

# 3. Register and chat
nemoclaw <sb> mcp add lucidlink --url "https://$IP:8443/mcp" --env LUCIDLINK_MCP_HTTP_BEARER --trusted-private-host "$IP"
nemoclaw <sb> exec -- openclaw agent --agent main -m "Use the lucidlink tools: create /mcp-smoke.txt with 'hello from NemoClaw', then read it back"
```

## NemoClaw v1 (preview)

NemoClaw v1, the unreleased `v1` branch, is declarative: a YAML config for `nemoclaw apply`, or OpenTofu providers
for OpenShell sandboxes and NeMo Fabric agents. `mcp add` is gone. [`nemoclaw-v1/`](./nemoclaw-v1) gives agents in
stock `nc-fabric` images a LucidLink filespace in both forms: a read-only team skills folder, a workspace that
outlives the sandbox, and the LucidLink MCP tools, with one service account per agent. The example runs an OpenClaw
researcher on NVIDIA Nemotron and a Claude Code coder on Claude. Setup, verification and limits are in
[`nemoclaw-v1/README.md`](./nemoclaw-v1).
