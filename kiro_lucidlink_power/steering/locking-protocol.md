# Locking protocol: the filespace is multi-writer

Load this before any write, edit, move, or delete on an existing path.

Humans and other agents may be editing the same files right now. Locks are
cooperative: they protect only writers who also claim. Your discipline IS
the protection.

## HARD PRECONDITION on write tools

These tools REQUIRE an active claim handle for the target path when that
path already exists:

`append_file`, `edit_lines`, `search_replace`, `write_file`, `copy_file`
(existing destination), `move_path`, `delete_path`.

Calling any of them on an existing path without holding a claim is a
protocol violation - there is no "quick edit" or "harmless append"
exemption. The ONLY exemption is creating a path that does not exist yet.
Before every write-tool call, check: do I hold a claim for this path?

## The claim protocol

1. Claim: `claim_file(path, mode="exclusive", blocking=false)`. Keep the
   returned `handle_id`.
2. If the result is `BLOCKED`: another writer holds the file. Do not fail
   and do not write anyway. Retry the claim a few times with short pauses;
   if it stays blocked, tell the user who/what might be editing and ask how
   to proceed.
3. Make the edit.
4. Release immediately: `release_file(handle_id)`. Never hold a claim while
   doing unrelated work, waiting on the user, or after the edit is done.

## Facts to remember

- `list_locks_held` shows only THIS session's locks. Other agents' locks are
  invisible to it - the only way to discover contention is a non-blocking
  claim attempt coming back `BLOCKED`.
- Never use `blocking=true` claims: they stall the whole session
  indefinitely with no way to report progress to the user.
- `claim_file` covers the file's size at claim time; bytes appended by you
  afterwards are not covered. For a file that may grow during the edit, use
  `lock_byte_range` with an explicit, generous length instead.
- New files need no claim (nothing to collide with until they exist), but
  re-opening and editing them later follows the protocol like any file.
