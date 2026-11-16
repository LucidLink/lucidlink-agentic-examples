output "agents" {
  description = "What invoking each agent needs."
  value = {
    for name, a in fabric_agent.agent : name => {
      workspace  = var.workspace
      sandbox    = name
      agent      = a.name
      runtime_id = a.runtime_id
    }
  }
}

output "volumes" {
  description = "Docker volumes created for LucidLink."
  value       = module.lucidlink.volumes
}
