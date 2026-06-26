---
name: "lucidlink"
displayName: "LucidLink"
description: "Read, search, edit, and organize files in a shared LucidLink filespace - safely, even when teammates and other agents are editing the same files at once. Powered by the LucidLink MCP server."
keywords: ["lucidlink", "filespace", "workspace"]
author: "LucidLink"
---

# LucidLink Filespace

You are operating on a shared LucidLink filespace - cloud storage that behaves
like a filesystem and is shared live with the user's team and other agents. You
read, write, search, and organize filespace files exclusively through the
`lucidlink` MCP tools. Always treat the filespace as **multi-writer**: claim
files before editing them and release them when done, because other humans and
agents may be working in the same files at the same time.

## Onboarding

Run these checks the first time the power is used, then report what you found.

### Step 1: Validate the toolchain

- The `lucidlink` MCP server launches via `uvx` (from [uv](https://docs.astral.sh/uv/)).
  Confirm `uv` is installed (`uv --version`). On first launch `uvx` builds the
  `lucidlink-mcp` package - give it a few seconds, then check the MCP panel
  lists the `lucidlink` tools.

### Step 2: Validate authentication

- The server needs a LucidLink **service account token**. Create one in the
  LucidLink workspace settings (service accounts), then place it in
  `~/.lucidlink/mcp-config.json`:

  ```json
  { "token": "<your-service-account-token>" }
  ```

  ```
  chmod 600 ~/.lucidlink/mcp-config.json
  ```

  A `LUCIDLINK_TOKEN` env value in `mcp.json` would **override** this file -
  leave it unset unless you mean to.

### Step 3: Orient

- Call `whoami` to confirm identity and token status.
- Call `list_filespaces` to see what the account can reach, then link one:
  if there is exactly one, link it with `link_filespace(name=...)`; if there
  are several, show the user the list and ask which to connect before linking.
  Confirm with `current_filespace`.
- Map the linked filespace with `tree` (set `max_depth`) so you have your
  bearings.

## When to load steering files

Load the matching `steering/` file before acting on that kind of task:

- Navigating, reading, or editing filespace files → `canonical-flow.md`
- Any write, edit, move, or delete on an existing path → `locking-protocol.md`
- Bulk replacements, deletes, or anything destructive → `safety.md`
- Managing the workspace itself - members, roles, permissions, groups,
  filespace lifecycle, audit trails, service accounts → `workspace-administration.md`

Locking and safety are not optional: any edit to an existing file requires the
claim protocol in `locking-protocol.md`, and any destructive or bulk operation
requires the precautions in `safety.md`.

## Tool quick reference

- **Orient:** `whoami`, `current_filespace`, `list_filespaces`, `link_filespace`,
  `tree`, `list_files`, `count_files`.
- **Search:** `find_files` (by name), `grep_files` (by content) - always narrow
  with `path_prefix` and `include_pattern` on large filespaces.
- **Read:** `read_lines` (plaintext, 1-indexed - prefer this for text),
  `read_file` (base64, for binary or exact whole-file bytes), `get_entry`
  (metadata/size).
- **Write text:** `edit_lines` (line-range replace), `search_replace` (literal
  or regex) - both support `dry_run=true`.
- **Write whole/new files:** `write_file`, `append_file` (both base64;
  `create_parents=true` to make missing dirs).
- **Organize:** `copy_file`, `move_path`, `create_directory`, `delete_path`.
- **Locks:** `claim_file`, `release_file`, `lock_byte_range`, `unlock_byte_range`,
  `list_locks_held`.

Paths are POSIX-style and absolute, rooted at the filespace (`/dir/file`).
Every write syncs to the hub automatically - there is no draft state, so write
only what is meant to be shared.
