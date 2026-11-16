# LucidLink for NemoClaw v1

A base recipe that connects NVIDIA NemoClaw v1 agents to a LucidLink filespace, declaratively. It comes in both of
NemoClaw v1's forms: a **YAML config for `nemoclaw apply`** and **plain OpenTofu** against the providers NemoClaw
ships. It uses stock `nc-fabric` images, and no token ends up in NemoClaw's state, plans or agent config.

> **Preview.** NemoClaw v1 is the unreleased `v1` branch of [NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw)
> and changes daily. This recipe was tested on commits `5716c39` and `fc50f2f` (see [Limits](#limits)).

## What agents get

| | How | In the sandbox |
|---|---|---|
| **LucidLink MCP tools** | `lucidlink-mcp` runs inside the sandbox as a stdio MCP server | Tools to list, read, write, lock and audit files (or the read-only subset) |
| **LucidLink folders** | The host mounts filespace folders; Docker volumes bind them into sandboxes | Ordinary directories: the agent's workspace, a shared team skills folder |

The example deploys two agents:

* **researcher** (OpenClaw): read-only MCP tools, and team skills from a read-only folder at `/sandbox/skills`.
* **coder** (Claude Code): read-write MCP tools, and its own folder on the filespace as `/sandbox/workspace`.

Each agent has its own LucidLink service account, so the filespace audit trail names the agent for every change,
and its grants are exactly what it may touch. Files outlive sandboxes, show up live in the LucidLink apps, and can
be restored from snapshots.

## What's in this folder

| Path | What |
|---|---|
| `yaml/` | `lucidlink-agents.yaml.tmpl` (the NemoClaw config), `prepare.sh` (builds the toolchain, creates and labels the volumes, renders the YAML), `lucidlink.env.example` |
| `examples/two-agents/` | The same two agents in OpenTofu, using `modules/lucidlink/`; `pin-providers.sh` pins your bundle's provider versions |
| `modules/lucidlink/` | OpenTofu module: Docker volumes (toolchain, credentials, folders) plus the mounts, egress policies and MCP server block for `openshell_sandbox` and `fabric_agent` |
| `host/` | `install-host.sh` (agent user, mounts, MCP tokens), `lucid-agent@.service` (one LucidLink daemon per mount), `agents-apply@.service` and `agents-apply.sh` (re-apply at boot) |
| `toolchain/Dockerfile` | Self-contained Python and `lucidlink-mcp` under `/opt/lucidlink`, copied into a volume that sandboxes mount read-only |
| `showcase/` | Two agents editing one shared file at the same time under LucidLink locks |

## How it works

```
host (Linux)                                              sandbox "coder" (uid 10001)
────────────────────────────────────────────────────      ─────────────────────────────────────────────
lucid-agent@2 (coder's account)   /srv/lucid-agent-coder ──▶ /sandbox/workspace          its own folder
lucid-agent@1 (team read-only)    /srv/lucid-ro-skills   ──▶ /sandbox/skills  (researcher, read-only)
/etc/lucid-agent/mcp-coder/token                          ──▶ /etc/lucidlink   read-only  its MCP token
toolchain volume                                          ──▶ /opt/lucidlink   read-only  lucidlink-mcp
                                                           egress: the LucidLink hub (TCP 443) and the
                                                           filespace's own bucket, from that Python only
```

* **Ownership.** A LucidLink FUSE mount shows every file as owned by the user running the daemon. The daemons run as
  `llagent`, with the sandbox uid (10001), so agents create and edit files with normal permissions. Each mount
  exposes one folder (`--root-point`).
* **Read-only.** A folder mounted with a read-only service account is read-only in LucidLink itself: every write
  gets `Read-only file system`, whatever Docker's `read_only` says.
* **Tokens.** Daemon tokens are root-only files passed on stdin. An MCP token is a read-only file in the sandbox.
  The agent runs as the same user as its MCP server, so it could read that token and use it directly: the egress
  policy keeps other programs away from LucidLink, but **the service account's grants are the real boundary**.
  `read_only` (`LUCIDLINK_MCP_READ_ONLY=1`) only hides write tools, so give read-only agents a read-only account.
  Tested: an agent that starts its own MCP server and calls `write_file` with a read-only token gets
  `permission denied: Authorization exception`.
* **Volumes.** OpenShell admits a named volume only with the labels `openshell.ai/sandbox-attachable=true` and
  `openshell.ai/sandbox-attachable-workspace=<workspace>`, and bind-backed volumes need `enable_bind_mounts` and
  `allow_driver_config` in the gateway's Docker driver. Docker volumes can't be changed, so each name includes a
  hash of its source: changing a folder creates a new volume and replaces only the sandboxes that use it.

## Quick start

### 1. Prerequisites

* A Linux x86_64 host with Docker, the NemoClaw v1 bundle and its `nc-fabric` images, pinned by digest.
* The [LucidLink Linux client](https://www.lucidlink.com/download) and `fuse3`.
* An Anthropic API key (any provider NemoClaw supports works; the example uses Anthropic).
* Three service accounts, minted in the LucidLink web app or with the LucidLink MCP admin tools:

  | Token | Grant | Used by |
  |---|---|---|
  | `team-ro.token` | read on `/agents/team-skills` | the skills mount |
  | `researcher.token` | read on `/agents/team-skills` (and whatever else it may read) | the researcher's MCP tools |
  | `coder.token` | read and write on `/agents/coder` | the coder's mount and MCP tools |

### 2. Host

Tokens are only ever read on stdin. Re-running a command with the same settings changes nothing.

```sh
sudo host/install-host.sh base
sudo host/install-host.sh mount 1 myfs.myworkspace /agents/team-skills /srv/lucid-ro-skills < team-ro.token
sudo host/install-host.sh mount 2 myfs.myworkspace /agents/coder /srv/lucid-agent-coder < coder.token
sudo host/install-host.sh mcp-token researcher < researcher.token
sudo host/install-host.sh mcp-token coder < coder.token
```

### 3. Agents, with YAML

This creates its own managed OpenShell gateway.

```sh
cd yaml
cp lucidlink.env.example lucidlink.env      # filespace, folders, credential directories, image digests
./prepare.sh                                # volumes and lucidlink-agents.yaml; no secrets involved
ANTHROPIC_API_KEY=... nemoclaw apply --state-dir .nemoclaw lucidlink-agents.yaml
```

Keep `.nemoclaw`: it is the deployment's state. `prepare.sh` gives the deployment a stable `metadata.uid` on its
first run, because the OpenShell workspace name derives from it and the volumes are labelled for that workspace.
NemoClaw's YAML has no anchors or variables, which is why a template is rendered and the network grants repeat for
each sandbox. After changing a folder or credential, run `prepare.sh` and `nemoclaw apply` again; `prepare.sh`
lists the volumes that are no longer used.

### 3. Or agents, with OpenTofu

This uses an existing OpenShell gateway, for example a NemoClaw deployment's managed gateway, with the Docker
driver settings above. The agents get their own workspace on it.

```sh
cd examples/two-agents
cp terraform.tfvars.example terraform.tfvars          # gateway, images, filespace, credentials, folders
./pin-providers.sh /path/to/bundle                    # NVIDIA's providers are pre-releases: pin them exactly
export TF_CLI_CONFIG_FILE=/path/to/providers.tfrc     # filesystem_mirror { path = "/path/to/bundle/providers" }
export ANTHROPIC_API_KEY=...
tofu init && tofu apply
```

### 4. Talk to an agent

`nemoclaw apply` prints the invoke command for each agent; with OpenTofu, `tofu output agents` lists the runtime
IDs. For example:

```sh
export OPENSHELL_GATEWAY_ENDPOINT=http://127.0.0.1:17671 OPENSHELL_WORKSPACE=<workspace>
printf '"List /agents/team-skills with your LucidLink tools."' | \
  openshell sandbox exec -n researcher --no-tty -- fabric-agent-ctl invoke --agent main --runtime-id <id> --input -
```

## Showcase: agents sharing one workspace

[`showcase/`](./showcase) runs two agents with different harnesses and their own accounts that append to one file
at the same time, taking a LucidLink lock for each change. No entry is lost, and the audit trail shows who wrote
what. That is what a filespace adds over a plain volume: shared state across sandboxes, hosts and people,
coordination through locks, and attribution.

## Operations

* **Reboots.** The `lucid-agent@` mounts start before Docker, and the gateway restarts the sandboxes, but agent
  runtimes don't survive a reboot (`nemoclaw plan` shows "agent runtime is not running"). `agents-apply@<name>`
  (install steps in the unit file; one instance per deployment, YAML or OpenTofu) re-applies at boot. It applies
  in-place changes only: a plan that would delete or replace something is re-checked for a few minutes and then
  left for a person to review. Instances run one at a time, so several deployments don't starve a small host.
* **Changes.** Anything fixed when a sandbox starts (instructions, model, mounts, policies, MCP server) replaces
  that agent's sandbox. Its files on LucidLink stay.
* **Never stop or unmount a LucidLink mount under running sandboxes.** The daemon stops responding. Stop the
  sandbox containers that use the mount first, restart `lucid-agent@<n>`, then apply again.
* **Tag images by commit.** NemoClaw's image build always tags `nc-fabric:<harness>`. Building another commit moves
  the tag, and digest references to the old image stop resolving. After each build, run
  `docker tag nc-fabric:<harness> nc-fabric:<harness>-<commit>`.
* **Restore.** Service accounts can't create snapshots, but they can mount the filespace's scheduled snapshots
  read-only (`lucid link --snapshot <id>` in a spare instance) to copy files back.
* **Teardown.** YAML: `nemoclaw destroy --state-dir .nemoclaw`, then remove the volumes `prepare.sh` made
  (`docker volume ls --filter label=lucidlink.com/recipe=nemoclaw-v1-yaml`). OpenTofu:
  `tofu destroy -var destroy=true`. On the host: `systemctl disable --now agents-apply@<name> lucid-agent@<n>` and
  remove what you no longer need from `/etc/lucid-agent`. Files on LucidLink stay.

## Limits

* **Linux x86_64 only.** The LucidLink Linux client and the Python SDK behind `lucidlink-mcp` are published for
  x86_64 only today, so this recipe doesn't run on arm64 hosts such as DGX Spark or DGX Station yet.
* **Tested commits.** `5716c39` (OpenShell 0.1.7, OpenTofu 1.12): everything, including the showcase.
  `fc50f2f` (OpenShell 0.1.8, OpenTofu 1.13): both forms deploy and the coder works, but at that commit OpenClaw
  can't call an Anthropic provider (with or without LucidLink), so the researcher's LucidLink tools were checked
  without the model.
* **Tool allowlists.** Fabric's per-tool MCP filters (`allowed_tools`) aren't available for OpenClaw or Claude Code
  yet. Use `read_only` for the tool list and a narrowly granted service account for enforcement.
* **Hermes** isn't in the example: at the tested commits, NemoClaw's Hermes image couldn't use an Anthropic provider.
* **Instructions.** OpenClaw only supports replacing its system prompt, so the example replaces it for OpenClaw
  and appends for Claude Code.
* **Storage.** The egress policy assumes path-style S3 URLs (`<host>/<bucket>/…`, bucket `lucid-fs-<filespace id>`),
  as the client uses with AWS S3. Other object stores need their own endpoints.
* **Toolchain.** The image pins its base by digest and `lucidlink-mcp` by version, not its dependencies. For strict
  reproducibility, build it once, push it, and use it by digest.
