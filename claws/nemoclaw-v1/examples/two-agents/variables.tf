variable "docker_host" {
  description = "Docker engine that runs the gateway's sandboxes."
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "gateway_endpoint" {
  description = "OpenShell gateway endpoint (its Docker driver needs enable_bind_mounts and allow_driver_config)."
  type        = string
}

variable "workspace" {
  description = "OpenShell workspace for these agents; also the Docker volume name prefix."
  type        = string
  default     = "lucidlink-agents"
}

variable "images" {
  description = "NemoClaw harness images, pinned by digest (nc-fabric@sha256:...)."
  type = object({
    openclaw = string
    claude   = string
  })
}

variable "inference" {
  description = <<-EOT
    Model endpoints by name. api: anthropic-messages or openai-completions. credential_env names the host environment
    variable that holds the API key; the provider reads it at apply and doesn't store it.
  EOT
  type = map(object({
    api            = string
    endpoint       = string
    credential_env = string
  }))
  default = {
    nvidia    = { api = "openai-completions", endpoint = "https://integrate.api.nvidia.com/v1", credential_env = "NVIDIA_API_KEY" }
    anthropic = { api = "anthropic-messages", endpoint = "https://api.anthropic.com", credential_env = "ANTHROPIC_API_KEY" }
  }

  validation {
    condition     = alltrue([for i in values(var.inference) : contains(["anthropic-messages", "openai-completions"], i.api) && startswith(i.endpoint, "https://")])
    error_message = "api must be anthropic-messages or openai-completions, and endpoint an https:// URL."
  }
}

variable "lucidlink_mcp_version" {
  description = "lucidlink-mcp release on PyPI for the toolchain image."
  type        = string
  default     = "1.0.1"
}

variable "filespace" {
  description = "See modules/lucidlink."
  type = object({
    name         = string
    id           = string
    storage_host = string
    bucket       = optional(string)
  })
}

variable "lucidlink_credentials" {
  description = "Token directories on the host by name (host/install-host.sh mcp-token)."
  type        = map(string)
}

variable "lucidlink_folders" {
  description = "LucidLink folders mounted on the host by lucid-agent@ units, by name."
  type = map(object({
    host_path = string
    read_only = optional(bool, false)
  }))
}

variable "agents" {
  description = <<-EOT
    Agents by sandbox name.
    harness:      openclaw | claude
    model:        { inference = <inference key>, name = <model id> }; Claude Code needs an anthropic-messages endpoint
    mcp:          null, or { credential = <lucidlink_credentials key>, read_only = bool }
    skills:       null, or a lucidlink_folders key mounted read-only at /sandbox/skills
    workspace:    null, or a lucidlink_folders key mounted at /sandbox/workspace
    instructions: optional system instructions: appended for Claude Code, replacing the default for OpenClaw
                  (the only mode its adapter supports), so write them as a complete prompt
  EOT
  type = map(object({
    harness      = string
    model        = object({ inference = string, name = string })
    mcp          = optional(object({ credential = string, read_only = optional(bool, false) }))
    skills       = optional(string)
    workspace    = optional(string)
    instructions = optional(string)
  }))

  validation {
    condition     = alltrue([for a in values(var.agents) : contains(["openclaw", "claude"], a.harness)])
    error_message = "harness must be openclaw or claude."
  }

  validation {
    condition     = alltrue([for a in values(var.agents) : contains(keys(var.inference), a.model.inference)])
    error_message = "Each agent's model.inference must be a key of var.inference."
  }

  validation {
    condition = alltrue([for a in values(var.agents) :
    a.harness != "claude" || try(var.inference[a.model.inference].api, "") == "anthropic-messages"])
    error_message = "Claude Code needs an anthropic-messages endpoint."
  }
}

variable "destroy" {
  description = "Permit deleting provider-owned objects; set for tofu destroy."
  type        = bool
  default     = false
}
