# Showcase: agents sharing one workspace

Two agents in separate NemoClaw v1 sandboxes, with different harnesses (OpenClaw and Claude Code) and their own
LucidLink service accounts, edit **one shared file** at the same time. Each change is made under a LucidLink lock
(`claim_file` → `read_file` → `write_file` → `release_file`), so no entry is lost, and the filespace audit
trail records every write under the agent that made it. People see the same file live in the LucidLink app.

This is what a filespace adds over a plain volume: live shared state across sandboxes, hosts and people,
coordination through locks, and attribution.

```sh
# Service accounts writer-a and writer-b, each with read and write on /agents/shared only.
sudo ../host/install-host.sh mcp-token writer-a < writer-a.token
sudo ../host/install-host.sh mcp-token writer-b < writer-b.token

cd ../examples/two-agents
./pin-providers.sh /path/to/bundle
export TF_CLI_CONFIG_FILE=/path/to/providers.tfrc NVIDIA_API_KEY=<nvidia-api-key> ANTHROPIC_API_KEY=<anthropic-api-key>
tofu init && tofu workspace new showcase
cp ../../showcase/showcase.tfvars.example ../../showcase/showcase.tfvars   # fill in
tofu apply -var-file=../../showcase/showcase.tfvars

OPENSHELL_GATEWAY_ENDPOINT=http://127.0.0.1:17671 FILESPACE=my-filespace BOARD=/agents/shared/board.md \
  ../../showcase/run.sh
```

`run.sh` resets the board and counts the result without an LLM: `../scripts/mcp-call.py` calls the MCP tools directly from
inside a writer's sandbox. For a boot-time `agents-apply@showcase` instance, add `TF_WORKSPACE=showcase` and
`TF_CLI_ARGS_plan=-var-file=<path to showcase.tfvars>` to its env file.

The agents use only the MCP tools here, so no host mount is needed. Locks are advisory: they only exclude writers
that also take them, which is why both agents' instructions require the claim. Tested: 5 entries from each agent,
written concurrently (they interleave in the file), none lost, and the audit trail shows 5 writes per agent.
