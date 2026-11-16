variable "workspace" {
  description = "OpenShell workspace name the sandboxes run in. Volumes are labelled for it; OpenShell refuses volumes labelled for another workspace."
  type        = string
}

variable "name_prefix" {
  description = "Prefix for Docker volume names."
  type        = string
  default     = "ll"
}

variable "filespace" {
  description = <<-EOT
    The LucidLink filespace.
    name:         short name the MCP server links (LUCIDLINK_FILESPACE), e.g. "my-filespace".
    id:           filespace UUID; names the hub host <id>.fs.lucidlink.com and the default bucket.
    storage_host: object store host, e.g. "s3.us-west-1.amazonaws.com" (lucid status: object store).
    bucket:       bucket name; defaults to lucid-fs-<id>.
  EOT
  type = object({
    name         = string
    id           = string
    storage_host = string
    bucket       = optional(string)
  })
}

variable "toolchain" {
  description = <<-EOT
    The LucidLink MCP toolchain, or null for folder mounts only.
    image:       image holding /opt/lucidlink (see toolchain/Dockerfile), ideally pinned by digest.
    interpreter: the real path of its Python (cat /opt/lucidlink/INTERPRETER in the image). OpenShell
                 matches egress to this executable, so only the MCP server reaches LucidLink.
  EOT
  type = object({
    image       = string
    interpreter = optional(string, "/opt/lucidlink/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12")
  })
  default = null
}

variable "credentials" {
  description = "Service-account token directories on the host, by name. Each holds a file named token, readable by the sandbox uid (10001) and nobody else; host/install-host.sh creates them. The token never enters OpenTofu."
  type        = map(string)
  default     = {}

  validation {
    condition     = alltrue([for d in values(var.credentials) : startswith(d, "/")])
    error_message = "Credential directories must be absolute host paths."
  }
}

variable "folders" {
  description = "LucidLink folders mounted on the host (lucid-agent@ units), by name. read_only is Docker's flag; for LucidLink-enforced read-only, mount them with a read-only service account."
  type = map(object({
    host_path = string
    read_only = optional(bool, false)
  }))
  default = {}

  validation {
    condition     = alltrue([for f in values(var.folders) : startswith(f.host_path, "/")])
    error_message = "Folder host_path values must be absolute host paths."
  }
}

variable "extra_hub_hosts" {
  description = "Additional LucidLink hosts the MCP server may reach on 443."
  type        = list(string)
  default     = []
}
