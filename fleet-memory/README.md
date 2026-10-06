# Fleet memory - shared memory for LangGraph agents on a filespace

Three LangGraph agents share memory as JSON files on a LucidLink filespace: one folder per
namespace, one file per memory, an exclusive lock on every update, and an audit trail that
attributes each write to the agent's own service account. The researcher and analyst write to
a shared folder, the reviewer can only read it, and each agent has a private folder the others
cannot even list.

- `lucidlink_store.py` - a LangGraph `BaseStore` over the LucidLink Python SDK
- `fleet_agent.py` - one agent; run it as `researcher`, `analyst` or `reviewer`
- `collision.py` - two agents write the same file at once, without and then with the lock
- `run_fleet.sh` - runs the three agents in order and keeps their logs

## Set up once, as an admin

1. Create these folders in the filespace, from a mount, the MCP server or the SDK:

   ```
   /memory/
   ├── shared/customers/
   └── agents/
       ├── researcher/
       ├── analyst/
       └── reviewer/
   ```

2. Create three [collaborator service accounts](https://support.lucidlink.com/hc/en-us/articles/48014583746573-Collaborator-Service-Accounts-Beta)
   with these grants:

   | Account | Read and write | Read only |
   |---|---|---|
   | `agent-researcher` | `/memory/agents/researcher`, `/memory/shared` | |
   | `agent-analyst` | `/memory/agents/analyst`, `/memory/shared` | |
   | `agent-reviewer` | `/memory/agents/reviewer` | `/memory/shared` |

   One prompt per account does it through the MCP server, see [scoped agents](../scoped-agents/README.md);
   each token is saved as an `sa-*.token` file in `~/.lucidlink`. Symlink or copy each one to
   `~/.lucidlink/agent-<role>.token` and `chmod 600` it.

3. Enable the [audit trail](https://support.lucidlink.com/hc/en-us/articles/31125255979533-Audit-Trail-with-New-LucidLink)
   on the filespace.

## Run

From this folder, with Python 3.11 or newer:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export LUCIDLINK_FILESPACE=<filespace name> ANTHROPIC_API_KEY=sk-ant-...

python collision.py take1     # VERDICT: LOST UPDATE
python collision.py take2     # VERDICT: BOTH LANDED
./run_fleet.sh                # researcher, analyst, reviewer -> run-<role>.log
```

What you should see from the first agent, in `run-researcher.log` (abridged):

```
[21:48:40] researcher on <host> — filespace <name>, root /memory
  tool  manage_shared_memory({"action": "create", "content": "Acme renewed their contract early."})
  tool  manage_shared_memory({"action": "create", "content": "Acme procurement requires a single annual invoice."})
  tool  manage_shared_memory({"action": "create", "content": "Acme's fiscal year ends in March."})
  ->    created memory a317684a-a4aa-4dc2-b98c-d257b6fca733
  ...
```

Then read the audit trail for `/memory`, from the LucidLink MCP server's `read_audit_trail`
or the admin console: every memory file is attributed to the service account that wrote it.

To use another model, install its LangChain package and set `FLEET_MODEL` to its
`provider:model` string.
