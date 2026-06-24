# ☁️ LucidLink Mode for IBM Bob

A custom mode that lets [IBM Bob](https://bob.ibm.com) work with files
in your [LucidLink](https://www.lucidlink.com) filespace - safely, even when
teammates (or other agents) are editing the same files at the same time.

Ask Bob things like:

- *"What's in the filespace?"*
- *"Summarize /briefs and write the summary to /briefs/SUMMARY.md"*
- *"Find every file mentioning ACME and fix the spelling to ACME Corp"*

Bob navigates the filespace, previews edits before applying them, and asks before
deleting anything.

## Quickstart

**You need:** IBM Bob, [uv](https://docs.astral.sh/uv/), and a LucidLink
**service account token**: create one in the LucidLink workspace settings
(service accounts).

1. **Get the code samples and open this folder in Bob:**

   ```
   git clone https://github.com/LucidLink/lucidlink-agentic-examples.git
   cd lucidlink-agentic-examples/ibm_bob_lucidlink_mode
   ```

   Open the `ibm_bob_lucidlink_mode/` folder in IBM Bob (this folder is its
   own Bob workspace - its `.bob/` lives here). The mode and MCP server config
   are picked up automatically from `.bob/` - the LucidLink MCP server itself
   is fetched on first launch (via `uvx`), nothing to install.

2. **Give it your token** - create `~/.lucidlink/mcp-config.json`:

   ```json
   { "token": "<your-service-account-token>" }
   ```

   ```
   chmod 600 ~/.lucidlink/mcp-config.json
   ```

3. **Ask your first question** open the Bob panel → **MCP** tab → `lucidlink` should
   list its tools. Pick **☁️ LucidLink** in the mode selector and ask:

   > What's in the filespace?

   Bob links your filespace automatically (if your account sees several,
   it will ask which one) and maps it with `tree`. That's it - you're in.

   Expect approval prompts whenever you ask Bob to *change* something:
   reads are pre-approved, but every write tool asks you first. That's by
   design - approve per call, or "Always allow" the tools you trust.

### Using it in your own projects

Copy the `.bob/` directory into any project root. Everything travels with
it: the mode, the MCP server config, and the rules.

### Installing it globally (every project)

Don't want to copy `.bob/` into each repo? Install the mode into Bob's global
config (`~/.bob/`) and **☁️ LucidLink** shows up in the mode picker for *every*
project. Three pieces move from the workspace `.bob/` to their home-level
equivalents:

1. **The mode** - merge the `lucidlink` entry from `.bob/custom_modes.yaml`
   into `~/.bob/settings/custom_modes.yaml` (note the `settings/` subdir; a
   fresh install starts as `customModes: []`).

2. **The rules** - copy the rules folder to the home-level path Bob reads for
   this mode:

   ```
   cp -R .bob/rules-lucidlink ~/.bob/rules-lucidlink
   ```

3. **The MCP server** - easiest is Bob's **MCP tab → add a Global server**
   using the `lucidlink` entry from `.bob/mcp.json`; Bob writes it to
   `~/.bob/settings/mcp_settings.json` in the right format. (You can edit that
   file by hand instead, but the UI avoids typos and keeps a single source of
   truth - that file is the one Bob's global MCP editor reads.)

Your token (`~/.lucidlink/mcp-config.json`) is already global, so nothing
changes there. Reload Bob, confirm `lucidlink` lists its tools in the MCP tab,
and the mode is available everywhere.

A project-local `.bob/` still wins where it exists, so you can override the
global setup per repo when you need to.

## What the mode actually does

Three rule files (in `.bob/rules-lucidlink/`) shape Bob's behavior whenever
the mode is active:

| | |
|---|---|
| **Canonical flow** | Orient with `tree`/`grep` before acting; read text with line-based tools; keep searches narrow on big filespaces. |
| **Locking protocol** | The filespace is multi-writer. Bob claims a file (non-blocking) before any edit, releases right after, and backs off with a clear message if someone else holds it.|
| **Safety** | Dry-run preview before bulk replacements, explicit confirmation before deletes, no slurping huge files, filespace content stays in the session. |

## Hardening options

- **Read-only server:** add `"env": { "LUCIDLINK_MCP_READ_ONLY": "1" }` to
  the server entry in `.bob/mcp.json` - analysis-only projects can't write
  at all.
- **Pin a filespace:** `"env": { "LUCIDLINK_FILESPACE": "<name>" }` skips
  the which-filespace question for multi-filespace accounts.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Auth errors / "token rejected" | Check `~/.lucidlink/mcp-config.json`. Careful: a `LUCIDLINK_TOKEN` in `mcp.json`'s `env` **overrides** the config file - remove placeholder values. |
| Mode missing from the picker | Reload the Bob window; confirm `.bob/custom_modes.yaml` is at the workspace root. |
| MCP server shows no tools | First launch builds the package - give it a few seconds and refresh the MCP tab. Check `uv` is installed. |
| "No filespace linked" | Account sees several filespaces: ask Bob to `list_filespaces` and link one, or pin via `LUCIDLINK_FILESPACE`. |
| Bob's claim is always `BLOCKED` | Someone (or some agent) holds the file - that's the protection working. Ask Bob to retry, or find the other writer. |

## Links

- [LucidLink MCP server on PyPI](https://pypi.org/project/lucidlink-mcp/)
