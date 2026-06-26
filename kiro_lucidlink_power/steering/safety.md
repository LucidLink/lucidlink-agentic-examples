# Safety rules

Load this before bulk replacements, deletes, or anything destructive.

## Destructive operations

- `delete_path`: only with the user's explicit confirmation in this
  conversation, even though the host prompts too. State exactly what will be
  deleted (use `count_files` for directories) before asking.
- DRY-RUN PRECONDITION: any `search_replace` or `edit_lines` call that can
  change more than one line or occurrence requires a `dry_run=true` call on
  THAT SAME file first. A successful dry run on one file does not validate
  the pattern for any other file - the same pattern can be destructive in
  the next file.
- Multi-file batches: work file by file - dry-run, check the preview
  actually matches the intent, apply, release, next file. If any preview
  looks unexpected (wrong count, wrong context), stop and show the user
  before applying anywhere else.
- `copy_file` refuses to overwrite by default - keep it that way. Before
  writing to a path you did not create, check it with `get_entry`.
- `move_path` over an existing destination is an overwrite: check first.

## Zero-knowledge encryption

- File content is end-to-end encrypted; plaintext exists only in this MCP
  session. Do not forward filespace content to external services, logs, or
  other tools unless the task requires it and the user knows.
- Filenames on the hub are HMAC-keyed indexes - but treat names as
  potentially sensitive anyway.

## Resource discipline

- Reads are capped (server-side read cap). Don't slurp large files: use
  `read_lines` ranges, `grep_files` with narrow `path_prefix` and
  `include_pattern`, and check sizes with `get_entry` first.
- Media and other large binaries: operate on metadata and paths; don't read
  content through the MCP unless explicitly needed.
- Do not `link_filespace` to a different filespace, or `unlink_filespace`,
  unless the user asks - switching mid-task silently changes what every
  path refers to.
