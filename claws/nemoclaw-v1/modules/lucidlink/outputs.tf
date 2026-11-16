# Everything is plain data for the caller's openshell_sandbox and fabric_agent blocks.

output "mcp" {
  description = <<-EOT
    Per credential: what an agent that runs the LucidLink MCP server needs.
    mounts:   Docker mounts for the sandbox's driver_config (token + toolchain, read-only).
    policies: managed network policies for the sandbox (hub over TCP, storage bucket over REST).
    server:   the fabric_agent mcp server (stdio, harness_native). Merge
              { LUCIDLINK_MCP_READ_ONLY = "1" } into env for a read-only tool set.
  EOT
  value = local.toolchain ? {
    for k, v in docker_volume.credential : k => {
      mounts = concat(
        [{ type = "volume", source = v.name, target = local.token_path, read_only = true }],
        local.toolchain_mount,
      )
      policies = local.mcp_policies
      server = {
        transport = "stdio"
        url       = local.launcher
        exposure  = "harness_native"
        env       = { LUCIDLINK_FILESPACE = var.filespace.name }
      }
    }
  } : {}
  depends_on = [docker_container.toolchain_copy]
}

output "folders" {
  description = "Per folder: source volume and read_only flag; the caller picks the target path."
  value = {
    for k, v in docker_volume.folder : k => { source = v.name, read_only = var.folders[k].read_only }
  }
}

output "volumes" {
  description = "All volume names created, for inspection and teardown."
  value = concat(
    [for v in docker_volume.toolchain : v.name],
    [for v in docker_volume.credential : v.name],
    [for v in docker_volume.folder : v.name],
  )
}
