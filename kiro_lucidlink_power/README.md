# LucidLink Power for Kiro

A custom [Kiro](https://kiro.dev) **Power** that lets Kiro work with files in
your [LucidLink](https://www.lucidlink.com) filespace - safely, even when
teammates (or other agents) are editing the same files at the same time.

A Power loads on demand: when your conversation mentions the filespace (or any
of the power's keywords), Kiro activates it and pulls in the LucidLink tools
and the working rules - no context bloat when you're not using it.

Ask Kiro things like:

- *"What's in the filespace?"*
- *"Summarize /briefs and write the summary to /briefs/SUMMARY.md"*
- *"Find every file mentioning ACME and fix the spelling to ACME Corp"*

Kiro navigates the filespace, previews edits before applying them, and asks
before deleting anything.

## What's in this power

```
kiro_lucidlink_power/
├── POWER.md        # metadata + keywords + onboarding + steering map
├── mcp.json        # the LucidLink MCP server (uvx lucidlink-mcp)
└── steering/
    ├── canonical-flow.md          # orient → read → write
    ├── locking-protocol.md        # claim before editing a shared file
    ├── safety.md                  # dry-run, confirm deletes, encryption
    └── workspace-administration.md # members, permissions, filespace lifecycle (opt-in)
```

## Quickstart

**You need:** [Kiro](https://kiro.dev), [uv](https://docs.astral.sh/uv/), and a
LucidLink **service account token**: create one in the LucidLink workspace
settings (service accounts).

1. **Get the code samples:**

   ```
   git clone https://github.com/LucidLink/lucidlink-agentic-examples.git
   cd lucidlink-agentic-examples
   ```

2. **Give it your token** - create `~/.lucidlink/mcp-config.json`:

   ```json
   { "token": "<your-service-account-token>" }
   ```

   ```
   chmod 600 ~/.lucidlink/mcp-config.json
   ```

3. **Import the power into Kiro:** open the **Powers** panel (the Ghosty icon
   with the lightning bolt) → **Add Custom Power** → **Import power from a
   folder** → select this `kiro_lucidlink_power/` directory.

   Kiro registers the `lucidlink` MCP server automatically (it writes it into
   `~/.kiro/settings/mcp.json`). The server itself is fetched on first launch
   via `uvx` - nothing to install. Click **Try the power** to run the
   onboarding checks.

4. **Ask your first question** - the power activates on keywords like
   *filespace*, *LucidLink*, or *workspace*:

   > What's in the filespace?

   Kiro links your filespace automatically (if your account sees several, it
   will ask which one) and maps it with `tree`. That's it - you're in.

   Expect approval prompts whenever you ask Kiro to *change* something: reads
   are pre-approved (the `autoApprove` list in `mcp.json`), but every write
   tool asks you first. That's by design - approve per call, or trust the
   tools you're comfortable with.

## What the power actually does

The steering files shape Kiro's behavior whenever the power is active. Kiro
loads them on demand using the map in `POWER.md`:

| | |
|---|---|
| **Canonical flow** | Orient with `tree`/`grep` before acting; read text with line-based tools; keep searches narrow on big filespaces. |
| **Locking protocol** | The filespace is multi-writer. Kiro claims a file (non-blocking) before any edit, releases right after, and backs off with a clear message if someone else holds it. |
| **Safety** | Dry-run preview before bulk replacements, explicit confirmation before deletes, no slurping huge files, filespace content stays in the session. |
| **Workspace administration** | Optional admin plane (members, roles, permissions, groups, filespace lifecycle). Off by default; when asked for an admin action whose tool is missing, Kiro walks you through enabling it instead of failing. |

## Workspace administration (opt-in)

By default the power only touches files inside a filespace. To let Kiro manage
the **workspace** - invite/remove members, roles, permissions, groups, create
or delete filespaces, audit trails - enable the admin toolset. You need
**Node 22+** installed (`node --version`). Then add an `env` block to the Power's server entry in
`~/.kiro/settings/mcp.json` (the Power nests its server under a top-level
`"powers"` key with a namespaced name) and reload Kiro:

```json
"env": { "LUCIDLINK_MCP_TOOLSETS": "admin" }
```

You don't have to edit it by hand - ask Kiro for an admin action and it walks
you through this same setup. See `steering/workspace-administration.md` for how
Kiro handles these (read-only listing tools vs. confirm-first changes).

## Hardening options

Set under the server's `env` in `mcp.json`:

- **Read-only server:** add `"env": { "LUCIDLINK_MCP_READ_ONLY": "1" }` to the
  `lucidlink` entry - analysis-only projects can't write at all.
- **Pin a filespace:** `"env": { "LUCIDLINK_FILESPACE": "<name>" }` skips the
  which-filespace question for multi-filespace accounts.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Auth errors / "token rejected" | Check `~/.lucidlink/mcp-config.json`. Careful: a `LUCIDLINK_TOKEN` in `mcp.json`'s `env` **overrides** the config file - remove placeholder values. |
| Power never activates | Make sure your message uses one of the keywords (filespace, LucidLink, shared storage…), or re-import the power and confirm it's enabled in the Powers panel. |
| MCP server shows no tools | First launch builds the package - give it a few seconds and refresh the MCP panel. Check `uv` is installed. |
| "No filespace linked" | Account sees several filespaces: ask Kiro to `list_filespaces` and link one, or pin via `LUCIDLINK_FILESPACE`. |
| Kiro's claim is always `BLOCKED` | Someone (or some agent) holds the file - that's the protection working. Ask Kiro to retry, or find the other writer. |

## Links

- [Kiro Powers docs](https://kiro.dev/docs/powers/)
- [LucidLink MCP server on PyPI](https://pypi.org/project/lucidlink-mcp/)
