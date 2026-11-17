# How it works

NemoClaw v1 leaves volumes and identities to the platform. This example supplies both from LucidLink, using only
documented NemoClaw and OpenShell features: named Docker volumes on the sandbox, network policy grants, and a stdio
MCP server in the agent configuration.

```text
host (Linux)                                               sandbox "coder" (uid 10001)
─────────────────────────────────────────────────────      ────────────────────────────────────────────────
lucid-agent@2 (coder's account)   /srv/lucid-agent-coder ──▶ /sandbox/workspace           its own folder
lucid-agent@1 (team read-only)    /srv/lucid-ro-skills   ──▶ /sandbox/skills  (researcher, read-only)
/etc/lucid-agent/mcp-coder/token                         ──▶ /etc/lucidlink    read-only  its MCP token
toolchain volume                                         ──▶ /opt/lucidlink    read-only  lucidlink-mcp
                                                            egress: the LucidLink hub (TCP 443) and the
                                                            filespace's own bucket, from that Python only
```

## Folders

The host runs one LucidLink daemon per mount (`lucid-agent@<n>`, a systemd unit). Each daemon signs in with a
service account and exposes one folder of the filespace (`--root-point`). A Docker volume binds that folder into the
sandbox.

* **Ownership.** A LucidLink FUSE mount shows every file as owned by the user that runs the daemon. The daemons run
  as `llagent`, with the sandbox uid (10001), so agents create and edit files with normal permissions.
* **Read-only.** A folder mounted with a read-only service account is read-only in LucidLink itself. Every write
  fails with `Read-only file system`, whatever Docker's `read_only` flag says.
* **Admission.** OpenShell admits a named volume only when it has the labels `openshell.ai/sandbox-attachable=true`
  and `openshell.ai/sandbox-attachable-workspace=<workspace>`. Bind-backed volumes also need `enable_bind_mounts`
  and `allow_driver_config` in the gateway's Docker driver configuration.
* **Volume names.** A Docker volume can't be changed, so each name includes a hash of its source. A changed folder
  gets a new volume, and only the sandboxes that use it are replaced.

## MCP tools

`toolchain/Dockerfile` builds a self-contained Python with `lucidlink-mcp` under `/opt/lucidlink`. `prepare.sh` (YAML)
or the OpenTofu module copies it into a volume that sandboxes mount read-only. The harness starts
`/opt/lucidlink/bin/lucidlink-mcp-launch` as a stdio MCP server. The launcher reads the token from
`/etc/lucidlink/token` and exits with an error if the file is missing.

`LUCIDLINK_MCP_READ_ONLY=1` hides the write tools. It doesn't enforce anything: see the next section.

## Identity and the security boundary

Each agent has its own LucidLink service account, so the filespace audit trail names the agent for every read and
write.

The agent runs as the same user as its MCP server, so it can read the token and use it directly. The network policy
keeps other programs in the sandbox away from LucidLink, but **the service account's grants are the real boundary**.
Give a read-only agent a read-only account. Tested: an agent that starts its own MCP server with a read-only token
and calls `write_file` gets `permission denied: Authorization exception`.

Daemon tokens are root-only files (`/etc/lucid-agent/<n>.token`, mode 0600) that systemd passes on stdin. MCP tokens
are files owned by the sandbox uid (mode 0400) in a read-only volume. No token is part of the NemoClaw configuration,
its state, its plans or the agent configuration.

## Network policy

Each sandbox gets two grants, both limited to the toolchain's Python binary:

| Grant | Endpoints | Why |
|---|---|---|
| `lucidlink-hub` | `api.lucidlink.com`, `discovery-service.lucidlink.com`, `<filespace id>.fs.lucidlink.com`, TCP 443 | Sign-in and the filespace metadata hub. The client pins its own TLS, so the grant uses `tls: skip`. |
| `lucidlink-storage` | The filespace's object store, HTTPS, enforced | Only the filespace's own bucket (`/<bucket>` and `/<bucket>/**`). |

The model endpoint gets its own grant, for `/v1/**` on the endpoint's host. NemoClaw adds it from the inference
provider in the YAML path; the OpenTofu example adds the same grant itself.

## Models

The researcher uses Nemotron through NVIDIA's API, which is OpenAI-compatible. You can switch it to Anthropic with
`RESEARCHER_PROVIDER` (YAML) or the agent's `model` (OpenTofu). The Claude Code adapter needs an endpoint that serves
Anthropic's Messages API. NVIDIA's API doesn't serve Nemotron models on that API, so the coder uses Anthropic.

OpenClaw must finish starting within one deadline, 60 seconds by default. On a busy host it can miss that, and the
apply fails with `openclaw_gateway_start_timeout`. The example sets `startup_timeout_seconds` to 75, the most that
the adapter accepts.

## The two forms

| | YAML | OpenTofu |
|---|---|---|
| Entry point | `yaml/prepare.sh`, then `nemoclaw apply` | `examples/two-agents`, `tofu apply` |
| Gateway | Creates its own managed gateway | Uses an existing gateway |
| Volumes | Created and labelled by `prepare.sh` | Created by `modules/lucidlink` |
| Reuse | The grants are defined once in `spec.grants`; each sandbox selects them with `grantRefs` | The module outputs the mounts, grants and MCP server block |

Both use stock `nc-fabric` images.

## Instructions

OpenClaw only supports replacing its system prompt. The OpenTofu example replaces it for OpenClaw and appends to it
for Claude Code.
