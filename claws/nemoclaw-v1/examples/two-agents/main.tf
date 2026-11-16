# Two agents on one LucidLink filespace, in plain OpenTofu against NemoClaw v1's providers. By default:
#
#   researcher  OpenClaw     read-only LucidLink MCP tools; team skills from a read-only folder
#   coder       Claude Code  LucidLink MCP tools; its own LucidLink folder as its workspace
#
# Stock nc-fabric images; the volumes come from modules/lucidlink and the host side from host/install-host.sh.

terraform {
  required_version = "~> 1.12"
  # The NVIDIA providers come from your NemoClaw bundle's filesystem mirror (TF_CLI_CONFIG_FILE). Their versions are
  # pre-releases that change with every bundle, and OpenTofu only selects a pre-release when pinned exactly:
  # ./pin-providers.sh <bundle dir> writes providers_override.tf with the bundle's versions.
  required_providers {
    docker    = { source = "registry.opentofu.org/kreuzwerker/docker", version = "~> 4.6" }
    openshell = { source = "registry.opentofu.org/nvidia/openshell" }
    fabric    = { source = "registry.opentofu.org/nvidia/fabric" }
  }
}

provider "docker" {
  host = var.docker_host
}
provider "openshell" {
  destroy = var.destroy
}
provider "fabric" {
  destroy = var.destroy
}

locals {
  harnesses = {
    # instructions: OpenClaw only supports replacing the system prompt; Claude Code keeps its own and appends.
    openclaw = { adapter_id = "nvidia.fabric.openclaw", image = var.images.openclaw, inference = "anthropic", instructions = "replace" }
    claude   = { adapter_id = "nvidia.fabric.claude", image = var.images.claude, inference = "anthropic-root", instructions = "append" }
  }

  # OpenClaw wants the endpoint with /v1; the Claude adapter appends /v1 itself (else /v1/v1/messages).
  inference = {
    "anthropic"      = "https://api.anthropic.com/v1"
    "anthropic-root" = "https://api.anthropic.com"
  }

  skills_path    = "/sandbox/skills"
  workspace_path = "/sandbox/workspace"
}

# ---------------------------------------------------------------- toolchain image

# The tag includes the version and a hash of the Dockerfile, and the toolchain volume is named after the tag, so
# rebuilding the same Dockerfile keeps the volume and the sandboxes.
locals {
  toolchain_tag = "lucidlink-mcp-toolchain:${var.lucidlink_mcp_version}-${substr(filesha1("${path.module}/../../toolchain/Dockerfile"), 0, 8)}"
}

resource "docker_image" "toolchain" {
  name         = local.toolchain_tag
  keep_locally = true
  build {
    context = "${path.module}/../../toolchain"
    build_args = {
      LUCIDLINK_MCP_VERSION = var.lucidlink_mcp_version
    }
  }
  triggers = {
    dockerfile = filesha1("${path.module}/../../toolchain/Dockerfile")
  }
}

# ---------------------------------------------------------------- LucidLink

module "lucidlink" {
  source      = "../../modules/lucidlink"
  workspace   = var.workspace
  name_prefix = var.workspace
  filespace   = var.filespace
  toolchain   = { image = docker_image.toolchain.name }
  credentials = var.lucidlink_credentials
  folders     = var.lucidlink_folders
}

# ---------------------------------------------------------------- OpenShell

data "openshell_gateway" "current" {
  endpoint                 = var.gateway_endpoint
  required_compute_drivers = ["docker"]
  wait_timeout_seconds     = 90 # at boot the gateway container may still be starting
}

locals {
  gateway = data.openshell_gateway.current.ref
}

resource "openshell_workspace" "this" {
  gateway = local.gateway
  name    = var.workspace
}

data "fabric_harness" "agent" {
  for_each   = var.agents
  image      = local.harnesses[each.value.harness].image
  adapter_id = local.harnesses[each.value.harness].adapter_id
  agent_name = "main"
  engine     = var.docker_host
}

locals {
  binaries = { for name, h in data.fabric_harness.agent : name => jsondecode(h.launch_json).binaries }

  inference_binaries = {
    for inf in keys(local.inference) : inf => sort(distinct(flatten([
      for name, a in var.agents : local.binaries[name] if local.harnesses[a.harness].inference == inf
    ])))
  }
}

resource "openshell_inference" "model" {
  for_each  = { for inf, bins in local.inference_binaries : inf => bins if length(bins) > 0 }
  gateway   = local.gateway
  workspace = openshell_workspace.this.ref
  name      = each.key
  api       = "anthropic-messages"
  binaries  = each.value
  server = {
    type              = "inference_server"
    endpoint          = local.inference[each.key]
    credential_env    = var.model.credential_env
    credential_source = ""
  }
}

locals {
  agents = {
    for name, a in var.agents : name => {
      harness   = a.harness
      inference = local.harnesses[a.harness].inference
      mcp       = a.mcp == null ? null : module.lucidlink.mcp[a.mcp.credential]
      read_only = a.mcp == null ? false : a.mcp.read_only
      mounts = concat(
        flatten([for c in(a.mcp == null ? [] : [a.mcp.credential]) : module.lucidlink.mcp[c].mounts]),
        a.skills == null ? [] : [{
          type = "volume", source = module.lucidlink.folders[a.skills].source, target = local.skills_path, read_only = true
        }],
        a.workspace == null ? [] : [{
          type      = "volume", source = module.lucidlink.folders[a.workspace].source, target = local.workspace_path
          read_only = module.lucidlink.folders[a.workspace].read_only
        }],
      )
      policies = concat(
        flatten([for c in(a.mcp == null ? [] : [a.mcp.credential]) : module.lucidlink.mcp[c].policies]),
        [{
          name     = "inference-${local.harnesses[a.harness].inference}"
          binaries = []
          endpoints = [{
            host = "api.anthropic.com", port = 443, protocol = "rest", path = "/v1/**", access = "full",
            tls  = null, enforcement = null, rules = []
          }]
        }],
      )
      config = {
        instructions = a.instructions
        model        = var.model.name
        skills       = a.skills != null
        mcp          = a.mcp
      }
    }
  }
}

# Fabric fixes an agent when its sandbox starts, so any change to these replaces the sandbox.
resource "terraform_data" "agent_config" {
  for_each = local.agents
  input = jsonencode({
    config   = each.value.config
    mounts   = each.value.mounts
    policies = each.value.policies
    server   = each.value.mcp == null ? null : each.value.mcp.server
  })
}

resource "openshell_sandbox" "agent" {
  for_each    = local.agents
  gateway     = local.gateway
  workspace   = openshell_workspace.this.ref
  owner       = openshell_workspace.this.owner
  name        = each.key
  image       = local.harnesses[each.value.harness].image
  launch_json = data.fabric_harness.agent[each.key].launch_json
  providers   = [openshell_inference.model[each.value.inference].ref]

  driver_config = jsonencode({ docker = { mounts = each.value.mounts } })

  policy {
    dynamic "managed" {
      for_each = { for p in each.value.policies : p.name => p }
      content {
        name = managed.key
        dynamic "binaries" {
          for_each = managed.value.binaries
          content {
            path = binaries.value
          }
        }
        dynamic "endpoints" {
          for_each = managed.value.endpoints
          content {
            host        = endpoints.value.host
            port        = endpoints.value.port
            tls         = endpoints.value.tls
            protocol    = endpoints.value.protocol
            enforcement = endpoints.value.enforcement
            path        = try(endpoints.value.path, null)
            access      = try(endpoints.value.access, null)
            dynamic "rules" {
              for_each = endpoints.value.rules
              content {
                allow {
                  method = rules.value.method
                  path   = rules.value.path
                }
              }
            }
          }
        }
      }
    }
  }

  lifecycle {
    replace_triggered_by = [terraform_data.agent_config[each.key]]
  }
}

resource "fabric_agent" "agent" {
  for_each = local.agents
  gateway  = local.gateway
  sandbox  = openshell_sandbox.agent[each.key].ref
  harness  = data.fabric_harness.agent[each.key].ref
  name     = "main"

  environment {
    provider  = "local"
    workspace = local.workspace_path
  }

  dynamic "instructions" {
    for_each = each.value.config.instructions == null ? [] : [each.value.config.instructions]
    content {
      system {
        content = instructions.value
        mode    = local.harnesses[each.value.harness].instructions
      }
    }
  }

  models "default" {
    provider    = "anthropic"
    model       = var.model.name
    base_url    = local.inference[each.value.inference]
    api_key_env = openshell_inference.model[each.value.inference].sandbox_env
  }

  runtime {
    artifacts = "/sandbox/artifacts"
  }

  dynamic "skills" {
    for_each = each.value.config.skills ? [local.skills_path] : []
    content {
      directories {
        folder = skills.value
      }
      duplicates = "reject"
    }
  }

  dynamic "mcp" {
    for_each = each.value.mcp == null ? [] : [each.value.mcp.server]
    content {
      servers "lucidlink" {
        transport = mcp.value.transport
        url       = mcp.value.url
        exposure  = mcp.value.exposure
        env       = merge(mcp.value.env, each.value.read_only ? { LUCIDLINK_MCP_READ_ONLY = "1" } : {})
      }
    }
  }
}
