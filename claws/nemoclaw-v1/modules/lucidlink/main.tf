# LucidLink for NemoClaw v1 sandboxes.
#
# Produces Docker volumes and the data an openshell_sandbox / fabric_agent needs:
#   - toolchain: the LucidLink MCP server (Python + lucidlink-mcp), copied from an image into a volume,
#     so any stock nc-fabric image can run it read-only from /opt/lucidlink;
#   - credentials: one volume per service-account token directory on the host, mounted at /etc/lucidlink.
#     The token is read on the host by the bind; it never enters OpenTofu state, plan or the agent config;
#   - folders: LucidLink folders mounted on the host (lucid-agent@ systemd units), bound into sandboxes;
#   - policies: OpenShell egress for the MCP server, scoped to the toolchain's interpreter.
#
# OpenShell admits a named volume only if it carries the two labels below, naming the workspace.
# Docker volumes can't be changed, so each name includes a hash of its source, and the new volume is created before
# the old one is removed: changing a folder or image replaces only the sandboxes that use it.

locals {
  labels = {
    "openshell.ai/sandbox-attachable"           = "true"
    "openshell.ai/sandbox-attachable-workspace" = var.workspace
    "app.kubernetes.io/managed-by"              = "opentofu"
    "lucidlink.com/module"                      = "lucidlink-nemoclaw"
  }

  bucket      = coalesce(var.filespace.bucket, "lucid-fs-${var.filespace.id}")
  toolchain   = var.toolchain != null
  token_path  = "/etc/lucidlink"
  tools_path  = "/opt/lucidlink"
  launcher    = "${local.tools_path}/bin/lucidlink-mcp-launch"
  interpreter = local.toolchain ? var.toolchain.interpreter : null

  short = { for k, v in merge(
    { for k, d in var.credentials : "cred-${k}" => d },
    { for k, f in var.folders : "dir-${k}" => f.host_path },
    local.toolchain ? { toolchain = var.toolchain.image } : {},
  ) : k => substr(sha1(v), 0, 8) }
}

resource "docker_volume" "toolchain" {
  count = local.toolchain ? 1 : 0
  name  = "${var.name_prefix}-toolchain-${local.short.toolchain}"

  dynamic "labels" {
    for_each = local.labels
    content {
      label = labels.key
      value = labels.value
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

# One-shot copy of /opt/lucidlink into the volume. Apply waits for it (attach) and fails if it failed, so no sandbox
# starts on a partial toolchain. It leaves a volume that already holds this toolchain alone (the container may be
# recreated while MCP servers use it), and fails if the image's interpreter isn't the one the egress policy names.
resource "docker_container" "toolchain_copy" {
  count        = local.toolchain ? 1 : 0
  name         = "${docker_volume.toolchain[0].name}-copy"
  image        = var.toolchain.image
  user         = "0:0"
  entrypoint   = ["/bin/sh", "-c"]
  command      = [local.copy_script]
  must_run     = false
  attach       = true
  logs         = true
  network_mode = "none"
  mounts {
    type   = "volume"
    source = docker_volume.toolchain[0].name
    target = "/dst"
  }
  lifecycle {
    create_before_destroy = true
    postcondition {
      condition     = self.exit_code == 0
      error_message = "Copying the LucidLink toolchain into ${docker_volume.toolchain[0].name} failed (exit ${coalesce(self.exit_code, -1)}): check the image and that its /opt/lucidlink/INTERPRETER matches toolchain.interpreter."
    }
  }
}

locals {
  copy_script = local.toolchain ? join("\n", [
    "set -eu",
    "want='${local.interpreter}'",
    "have=$(cat ${local.tools_path}/INTERPRETER)",
    "[ \"$have\" = \"$want\" ] || { echo \"image interpreter $have != policy interpreter $want\" >&2; exit 3; }",
    "if [ \"$(cat /dst/INTERPRETER 2>/dev/null || true)\" = \"$want\" ] && [ -x /dst/bin/lucidlink-mcp-launch ]; then echo 'toolchain already present'; exit 0; fi",
    "rm -rf /dst/* && cp -a ${local.tools_path}/. /dst/ && test -x /dst/bin/lucidlink-mcp-launch && echo 'toolchain copied'",
  ]) : ""
}

resource "docker_volume" "credential" {
  for_each = var.credentials
  name     = "${var.name_prefix}-cred-${each.key}-${local.short["cred-${each.key}"]}"
  driver   = "local"
  driver_opts = {
    type   = "none"
    o      = "bind"
    device = each.value
  }
  dynamic "labels" {
    for_each = local.labels
    content {
      label = labels.key
      value = labels.value
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "docker_volume" "folder" {
  for_each = var.folders
  name     = "${var.name_prefix}-dir-${each.key}-${local.short["dir-${each.key}"]}"
  driver   = "local"
  driver_opts = {
    type   = "none"
    o      = "bind"
    device = each.value.host_path
  }
  dynamic "labels" {
    for_each = local.labels
    content {
      label = labels.key
      value = labels.value
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

locals {
  hub_endpoints = [
    for host in concat(
      ["api.lucidlink.com", "discovery-service.lucidlink.com", "${var.filespace.id}.fs.lucidlink.com"],
      var.extra_hub_hosts,
    ) : { host = host, port = 443, tls = "skip", protocol = null, enforcement = null, rules = [] }
  ]

  # The filespace's own bucket only; OpenShell denies any other bucket on the same host. Assumes path-style S3
  # URLs (<host>/<bucket>/...), as the LucidLink client uses with AWS S3.
  storage_endpoints = [{
    host        = var.filespace.storage_host
    port        = 443
    tls         = null
    protocol    = "rest"
    enforcement = "enforce"
    rules = [
      { method = "*", path = "/${local.bucket}" },
      { method = "*", path = "/${local.bucket}/**" },
    ]
  }]

  # Only exposed through output.mcp, which is empty without a toolchain.
  mcp_policies = [
    { name = "lucidlink-hub", binaries = [local.interpreter], endpoints = local.hub_endpoints },
    { name = "lucidlink-storage", binaries = [local.interpreter], endpoints = local.storage_endpoints },
  ]

  toolchain_mount = local.toolchain ? [{
    type = "volume", source = docker_volume.toolchain[0].name, target = local.tools_path, read_only = true
  }] : []
}
