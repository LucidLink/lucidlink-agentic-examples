# Workspace administration

Load this when the task is about the LucidLink **workspace** rather than files
inside a filespace: inviting or removing members, roles and permissions, groups,
creating/renaming/deleting filespaces, audit trails, service accounts, or
direct links.

## Admin tools are OFF by default - enable them first

The admin tool plane is opt-in. If it is not enabled, tools like
`invite_member_admin` simply will not be available, and you should NOT treat
that as "the operation failed" - it means the power needs setup. Stop and walk
the user through enabling it:

1. **Node** must be installed (Node 22+). The admin shim ships with the MCP
   server, so Node on the user's PATH is the only extra requirement. Check
   with `node --version`.

2. **Turn on the admin toolset** by adding an `env` block to the power's
   server entry in Kiro's MCP settings (`~/.kiro/settings/mcp.json`). When a
   power is installed, Kiro nests its server under a top-level `"powers"` key
   and namespaces the name - so edit the entry there, NOT a top-level
   `mcpServers` one:

   ```json
   {
     "powers": {
       "mcpServers": {
         "power-kiro-lucidlink-power-lucidlink": {
           "command": "uvx",
           "args": ["lucidlink-mcp"],
           "env": { "LUCIDLINK_MCP_TOOLSETS": "admin" },
           "autoApprove": ["whoami", "list_filespaces", "link_filespace", "tree", "read_file"]
         }
       }
     }
   }
   ```

   Add only the `env` line; leave the generated `command`/`args`/`autoApprove`
   as Kiro wrote them. The exact namespaced key may differ - match whatever
   the `lucidlink` server is called under `powers.mcpServers`.

3. **Reload Kiro** (or restart the server from the MCP panel) so it relaunches
   with the admin tools registered.

When the user asks for an admin action and the admin tools aren't present, do
this setup walkthrough instead of failing silently.

## These operations are workspace-wide and high-stakes

Filespace edits affect files; admin actions affect people, access, and whole
filespaces. None of the admin tools are in `autoApprove` - every call prompts,
by design. On top of that:

- **Always confirm destructive admin actions in the conversation first**, and
  state exactly who/what is affected: inviting or removing a member, changing a
  member's role, revoking a permission, deleting or renaming a filespace or
  group, minting or deleting a service account, disabling an audit trail.
- **Read before you write.** Resolve the target first with the read-only admin
  tools (e.g. `find_member_admin` / `list_workspace_members_admin` to get a
  member id, `list_workspace_filespaces_admin` to get a filespace id) so you
  act on the right id, then perform the change.
- Member listings can be **masked** by default; only pass `unmask=true` when
  the user needs the real email/identity and is entitled to see it.

## Tool reference (admin plane)

**Read-only (safe to explore):** `whoami_admin`, `workspace_summary_admin`,
`list_workspace_filespaces_admin`, `get_filespace_info_admin`,
`list_workspace_members_admin`, `find_member_admin`,
`list_workspace_groups_admin`, `list_group_members_admin`,
`list_service_accounts_admin`, `list_permissions_admin`,
`get_audit_trail_status_admin`, `list_storage_providers_admin`.

**Additive (create/grant - confirm intent):** `grant_permission_admin`,
`enable_audit_trail_admin`, `create_workspace_group_admin`,
`add_group_member_admin`, `invite_member_admin` (invite by email with a role).

**Destructive (confirm explicitly, name the target):**
`remove_member_admin`, `change_member_role_admin`, `revoke_permission_admin`,
`rename_filespace_admin`, `delete_filespace_admin`, `create_filespace_admin`,
`rename_workspace_group_admin`, `delete_workspace_group_admin`,
`mint_service_account_admin`, `delete_service_account_admin`,
`disable_audit_trail_admin`, `generate_direct_link_admin`.
