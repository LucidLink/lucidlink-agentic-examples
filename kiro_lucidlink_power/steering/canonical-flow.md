# Canonical flow: working with the filespace

Load this when navigating, reading, or editing files in a LucidLink filespace.

## Session start

- Lead with `list_filespaces` so the choice is explicit: if there is exactly
  one, link it with `link_filespace(name=...)`; if there are several, ask the
  user which one before linking. Confirm with `current_filespace`.
- The server auto-links on the first file operation when the choice is
  unambiguous - but don't rely on that when several exist; an operation will
  just report no/ambiguous link.
- `whoami` shows identity, token status, and what is linked - use it when
  unsure about session state.

## Orientation before work

- Map unfamiliar territory with `tree` (set `max_depth`) or `list_files`.
- Before grepping a large area, gauge it with `count_files`. Walking the
  tree is slower than local disk: always narrow `grep_files` / `find_files`
  with `path_prefix` and `include_pattern`.

## Reading

- Text files: use `read_lines` (plaintext, 1-indexed, numbered). Read the
  range you need, not the whole file.
- `read_file` returns base64 (binary-safe). Use it only for binary content
  or when you genuinely need exact whole-file bytes; decode before reasoning
  about text.

## Writing and editing

- Edit existing text files with `edit_lines` (line-range replace) or
  `search_replace` (literal or regex). Both accept plaintext and support
  `dry_run=true` - preview any multi-line or repeated replacement first.
- Create new files with `write_file`; content must be base64-encoded
  (`create_parents=true` to make missing directories). Appends:
  `append_file`, also base64.
- Paths are POSIX-style and absolute, rooted at the filespace: `/dir/file`.
- Every write syncs to the hub automatically - teammates see it within
  seconds. There is no "draft" state: write what is meant to be shared.
- Any edit to an EXISTING path requires the claim protocol first - see
  `locking-protocol.md`. Bulk or destructive work requires `safety.md`.
