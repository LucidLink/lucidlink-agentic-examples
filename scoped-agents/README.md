# Scoped agents - least-privilege service accounts, minted by agents

Your AI agent can onboard *other* agents. Through the
[LucidLink MCP server](https://pypi.org/project/lucidlink-mcp/), an agent
running under an admin service account can mint **collaborator service
accounts** - machine teammates that see **nothing** until explicitly granted -
hand one a single folder of your filespace, and let a worker agent operate
inside that bubble. Anything outside the grant is simply invisible to the
worker.

Everything below is done by talking to your agent in natural language. No SDK
code, no REST calls, no token ever shown to the agent.

## Prerequisites

- `lucidlink-mcp` installed and configured with an **admin** service-account
  token ([Getting Started with Service Accounts](https://support.lucidlink.com/hc/en-us/articles/40222074543757-Getting-Started-with-Service-Accounts-API-Authentication)).
- Any MCP-capable agent (Claude Code, Claude Desktop, Cursor, a
  [terminal agent](../claws), ...).
- A folder in your filespace to hand to the worker, e.g. `/projects/alpha`.

## 1. Provision a scoped account - one prompt

> Mint a collaborator service account called "renderer", grant it read-write
> on /projects/alpha in my filespace, and register it as an account for this
> session.

Behind the scenes, the MCP tools create the account, grant it the folder, and
save its key to a local file. The agent never sees the key, and the account is
ready to use in the current session right away.

## 2. Step into the bubble

> Switch to the renderer account. What can you see?

One filespace, one folder: `/projects/alpha`. The agent has no knowledge of
anything outside its grant - other folders simply don't exist for it. Ask it
to `whoami` and it identifies as `renderer`, not as your admin account.

> Switch back to the default account.

Your main agent is the admin again. Both accounts stay live side by side.

## 3. Single-use credentials - a one-way airlock

For one-shot jobs, mint the credential so it self-destructs:

> Mint a single-use collaborator service account called "ingest-once", grant
> it read-write on /uploads/incoming, and register it.

Single-use means exactly that:

- **Before the first mount** the token is a normal credential (it can list
  what it's been granted into).
- **Mounting the filespace consumes it** - the running session keeps working
  for as long as it stays connected.
- **It can't be reused**: no second mount, and new API calls are rejected
  with `Single use service identity already consumed`.

Time-boxed credentials work the same way with an expiry instead:

> ...with a credential that expires Friday at 18:00 UTC.

## 4. Hand it to a real worker

The scoped account isn't tied to your session - the minted token file *is* the
worker's whole identity. On the worker's own machine (a CI job, a render
node, a teammate's laptop):

```bash
uv tool install lucidlink-mcp
lucidlink-mcp-setup        # paste the token from the sa-*.token file
```

The worker's agent can only reach the folders its account was granted - it
cannot list, read, or even learn the names of anything else, no matter what
it's asked. Every write it makes lands in the audit trail under its own name.

Two notes:

- `lucidlink-mcp-setup` sets the default identity for every MCP client on
  that machine - run it on the worker's machine, not your own.
- The worker doesn't have to be an MCP harness: set `LUCIDLINK_TOKEN` to the
  minted token and any of the [framework examples](../frameworks) - LangChain,
  CrewAI, the Claude Agent SDK, ... - runs under the scoped account too.

## 5. Teardown - one prompt again

> Delete the renderer service account.

The principal, its grants, its credentials, and the local token file all go
with it.

## Notes

- Requires `lucidlink-mcp` >= 0.3.0 (service-account tool surface).
- Only admin service accounts can mint collaborator service accounts - a
  collaborator can never escalate its own access.
- Accounts registered in-session last until the session ends. To keep a
  scoped account permanently on a machine, run
  `lucidlink-mcp-setup --account NAME` and paste its token.
