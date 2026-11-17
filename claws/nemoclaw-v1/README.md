# LucidLink Filespace for NemoClaw Agents

| Catalog field | Value |
| --- | --- |
| Description | Gives NemoClaw v1 agents a LucidLink filespace: shared team skills, a persistent folder per agent, and file tools under each agent's own identity, with every change in the audit trail. |
| Industry | ✨ Other |
| Requirements | Linux x86-64 · Docker · NemoClaw v1 preview bundle and images · LucidLink filespace and service accounts · NVIDIA and Anthropic API keys |
| NemoClaw | 0.1.0 |
| Harness | OpenClaw 2026.9.34 |
| OpenShell | 0.1.8 |
| Reviewed | 2026-11-17 |
| Contributor | LucidLink |

This example was contributed by [LucidLink](https://www.lucidlink.com). For questions or support, contact
[support@lucidlink.com](mailto:support@lucidlink.com).

NemoClaw v1 runs each agent in an OpenShell sandbox and leaves storage and identity to the platform. This example
supplies both from a LucidLink filespace, using NemoClaw as designed: Docker volumes on the sandbox, network policy
grants, and a stdio MCP server in the agent configuration. It uses stock `nc-fabric` images. No secret is part of
the NemoClaw configuration, its state or its plans.

> **Preview.** NemoClaw v1 is the unreleased `v1` branch of [NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw)
> and changes daily. This example names the commits it was tested on.

## What agents get

* **Team skills.** One read-only folder of skills, shared by every agent and edited by people in the LucidLink apps.
* **A persistent workspace.** Each agent's working folder lives on the filespace, outlives its sandbox, shows up live
  for people, and can be restored from snapshots.
* **Their own identity.** Each agent signs in with its own LucidLink service account. Its grants define what it can
  touch, and the filespace audit trail names it for every change.
* **File tools.** `lucidlink-mcp` runs inside the sandbox and gives the agent tools to list, read, write, lock and
  audit files (or only the read-only tools).

The example deploys two agents:

| Agent | Harness | Model | LucidLink |
|---|---|---|---|
| `researcher` | OpenClaw | NVIDIA Nemotron, through the NVIDIA API | Read-only tools; team skills at `/sandbox/skills` |
| `coder` | Claude Code | Anthropic Claude | Read and write tools; its own folder at `/sandbox/workspace` |

[`showcase/`](showcase) adds two agents that edit one shared file at the same time under LucidLink locks.

## Requirements

* A Linux x86_64 host with Docker. The LucidLink Linux client is published for x86_64 only.
* The NemoClaw v1 bundle and the `nc-fabric` OpenClaw and Claude images, built from source. See
  [Get NemoClaw v1](docs/nemoclaw-v1.md).
* The LucidLink Linux client and `fuse3` (installed in step 1), plus `jq` and `gettext-base` (for `envsubst`).
* A LucidLink filespace and three service accounts, created in the LucidLink web app:

  | Token file | Grant | Used by |
  |---|---|---|
  | `team-ro.token` | Read on `/agents/team-skills` | The skills mount |
  | `researcher.token` | Read on `/agents/team-skills` | The researcher's MCP tools |
  | `coder.token` | Read and write on `/agents/coder` | The coder's mount and MCP tools |

* An NVIDIA API key from [build.nvidia.com](https://build.nvidia.com) and an Anthropic API key.

## Credentials and secrets

* Service account tokens are read only from standard input. `install-host.sh` stores the daemon tokens as root-only
  files and the MCP tokens as read-only files for the sandbox user.
* Model API keys stay in the environment of `nemoclaw apply` or `tofu apply`. NemoClaw and OpenShell pass them to the
  model endpoint. They aren't written to the configuration or the state.
* An agent can read its own MCP token. The service account's grants are the security boundary, so give the
  researcher a read-only account. See [How it works](docs/how-it-works.md#identity-and-the-security-boundary).

## Setup

### 1. Prepare the host

Install the LucidLink client and FUSE:

```bash
curl -fsSLo /tmp/lucidlink.deb https://www.lucidlink.com/download/new-ll-latest/linux-deb/stable/
sudo apt-get install -y /tmp/lucidlink.deb fuse3
```

Then run these commands from this folder. Re-running a command with the same settings changes nothing.

```bash
sudo host/install-host.sh base
sudo host/install-host.sh mount 1 <filespace>.<workspace> /agents/team-skills /srv/lucid-ro-skills < team-ro.token
sudo host/install-host.sh mount 2 <filespace>.<workspace> /agents/coder /srv/lucid-agent-coder < coder.token
sudo host/install-host.sh mcp-token researcher < researcher.token
sudo host/install-host.sh mcp-token coder < coder.token
```

Each `mount` prints `mount ok: <path> (10001:10001)`.

### 2. Deploy the agents with YAML

This path creates its own managed OpenShell gateway.

```bash
cd yaml
cp lucidlink.env.example lucidlink.env    # set the filespace, folders and image digests
./prepare.sh
NVIDIA_API_KEY=<nvidia-api-key> ANTHROPIC_API_KEY=<anthropic-api-key> \
  nemoclaw apply --state-dir .nemoclaw lucidlink-agents.yaml
```

`prepare.sh` builds the toolchain image, creates and labels the volumes, and renders `lucidlink-agents.yaml`. Keep
the `.nemoclaw` directory: it holds the deployment's state.

### 2. Or deploy the agents with OpenTofu

This path uses an existing OpenShell gateway, such as the managed gateway of a NemoClaw deployment, whose Docker
driver allows bind-backed volumes ([details](docs/how-it-works.md#folders)).

```bash
cd examples/two-agents
cp terraform.tfvars.example terraform.tfvars          # set the gateway, images, filespace and folders
./pin-providers.sh /path/to/bundle
export TF_CLI_CONFIG_FILE=/path/to/providers.tfrc     # a filesystem_mirror for /path/to/bundle/providers
export NVIDIA_API_KEY=<nvidia-api-key> ANTHROPIC_API_KEY=<anthropic-api-key>
tofu init && tofu apply
```

## Sandbox, network and policy permissions

| Sandbox | Mounts | Network grants (besides the model endpoint) |
|---|---|---|
| `researcher` | `/sandbox/skills` read-only, `/opt/lucidlink` and `/etc/lucidlink` read-only | LucidLink hub and the filespace's bucket, for the toolchain's Python only |
| `coder` | `/sandbox/workspace` read-write, `/opt/lucidlink` and `/etc/lucidlink` read-only | The same |

Both sandboxes use the `isolated` network tier. The gateway must set `allow_driver_config` and `enable_bind_mounts`
in its Docker driver configuration; the YAML path sets them.

## Verification

`scripts/verify.sh` checks both sandboxes from the host, without a model:

* The researcher sees the team skills, and both the folder and its service account refuse writes.
* A file that the coder writes in `/sandbox/workspace` is on the filespace in its folder.
* Programs other than the MCP server can't reach LucidLink.

`nemoclaw apply` prints the workspace and each agent's runtime ID; with OpenTofu, run `tofu output agents`. Set
`RESEARCHER_RUNTIME` to also ask the researcher, through its model, to list the skills folder with its tools.

```bash
OPENSHELL_GATEWAY_ENDPOINT=http://127.0.0.1:17671 OPENSHELL_WORKSPACE=<workspace> \
FILESPACE=<filespace> SKILLS_PATH=/agents/team-skills CODER_PATH=/agents/coder \
RESEARCHER_RUNTIME=<runtime-id> scripts/verify.sh
```

Every line starts with `ok` when the deployment works. The script exits with status 1 if a check fails.

To talk to an agent, use the invoke command that `nemoclaw apply` prints for it.

## Startup and shutdown

After a reboot, the LucidLink mounts start before Docker and the gateway restarts the sandboxes, but agent runtimes
must be applied again. `host/agents-apply@.service` does this at boot. See [Operations](docs/operations.md).

## Cleanup

* YAML: `nemoclaw destroy --state-dir .nemoclaw`, then
  `docker volume ls -q --filter label=lucidlink.com/recipe=nemoclaw-v1-yaml | xargs -r docker volume rm`.
* OpenTofu: `tofu destroy -var destroy=true`.
* Host: `sudo systemctl disable --now lucid-agent@1 lucid-agent@2`, then remove `/etc/lucid-agent`.

Files on the filespace stay. Delete the service accounts in the LucidLink web app when you no longer need them.

## Known limitations

* **Linux x86_64 only.** The LucidLink Linux client and the Python SDK behind `lucidlink-mcp` are published for
  x86_64 only. This example doesn't run on arm64 hosts such as DGX Spark yet.
* **Preview commits.** Tested on NemoClaw v1 commit `ce910d0`. The YAML uses `spec.grants` and `agent.mcp`, which
  need commit `9aff1c4` or later. The OpenTofu example also ran on `5716c39` and `fc50f2f`.
* **Claude Code needs an Anthropic Messages endpoint.** NVIDIA's API doesn't serve Nemotron models on that API, so
  the coder uses Anthropic.
* **Tool allowlists.** Fabric's per-tool MCP filters aren't available for OpenClaw or Claude Code. `read_only` trims
  the tool list; the service account's grants enforce it.
* **Object storage.** The storage grant assumes path-style S3 URLs (`<host>/<bucket>/…`), as the LucidLink client
  uses with AWS S3. Other object stores need their own endpoints.

## Files

| Path | Contents |
|---|---|
| `yaml/` | The NemoClaw configuration template, `prepare.sh` and `lucidlink.env.example` |
| `examples/two-agents/` | The same agents in OpenTofu, using `modules/lucidlink/` |
| `modules/lucidlink/` | OpenTofu module: volumes, mounts, network grants and the MCP server block |
| `host/` | `install-host.sh`, the `lucid-agent@` mount unit and the `agents-apply@` boot unit |
| `toolchain/` | The Dockerfile for the in-sandbox Python and `lucidlink-mcp` |
| `scripts/verify.sh` | The verification script |
| `showcase/` | Two agents sharing one file under LucidLink locks |
| `docs/` | [How it works](docs/how-it-works.md), [Operations](docs/operations.md), [Get NemoClaw v1](docs/nemoclaw-v1.md) |
