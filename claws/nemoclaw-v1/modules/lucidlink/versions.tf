terraform {
  required_version = "~> 1.12"
  required_providers {
    docker = { source = "registry.opentofu.org/kreuzwerker/docker", version = "~> 4.6" }
  }
}
