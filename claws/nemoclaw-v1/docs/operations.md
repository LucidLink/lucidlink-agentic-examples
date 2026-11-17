# Operations

## Startup after a reboot

The `lucid-agent@<n>` units start before Docker, and the OpenShell gateway restarts the sandboxes. Agent runtimes
don't survive a reboot: `nemoclaw plan` shows them as `agent runtime is not running`.

`host/agents-apply@.service` runs `host/agents-apply.sh` at boot, once per deployment (YAML or OpenTofu). It applies
in-place changes only:

* No changes: it exits.
* Only in-place updates: it applies them. For NemoClaw, it first requires two plans taken 20 seconds apart to match.
* A plan that deletes or replaces something: it checks again every 30 seconds, six times (right after boot, a
  sandbox that the gateway is still restarting can look replaceable). If the plan still deletes or replaces
  something, it exits with status 2 and leaves the change for a person to review.

Instances run one at a time, so several deployments don't starve a small host.

To install it for one deployment:

1. Copy the example to a fixed location, for example `/opt/lucidlink-nemoclaw`, and set `User=` in the unit.
2. Run `sudo install -m 0644 host/agents-apply@.service /etc/systemd/system/`.
3. Write `/etc/lucid-agent/apply-<name>.env` (owned by root, mode 0600) with the settings listed at the top of
   `host/agents-apply.sh`, including the model API keys.
4. Run `sudo systemctl daemon-reload && sudo systemctl enable agents-apply@<name>`.

## Changes

Fabric fixes an agent's configuration when its sandbox starts. Changing instructions, the model, mounts, policies
or the MCP server replaces that agent's sandbox. Its files on LucidLink stay.

* YAML: after changing a folder or a credential directory, run `prepare.sh` and `nemoclaw apply` again.
  `prepare.sh` lists the volumes that are no longer used.
* OpenTofu: run `tofu apply`.

## LucidLink mounts

**Don't stop or unmount a LucidLink mount while sandboxes use it.** The daemon stops responding and ignores
`SIGTERM`. To change a mount:

1. Stop the sandbox containers that use it (`docker stop <container>`).
2. Run `sudo host/install-host.sh mount --force <n> ...`, or `sudo systemctl restart lucid-agent@<n>`.
3. Apply the deployment again.

A daemon signs in from its token on every start. It doesn't keep a session.

## Images

NemoClaw's image build always tags `nc-fabric:<harness>`. Building another commit moves that tag, and digest
references to the old image stop resolving. After each build, tag the image with its commit:

```sh
docker tag nc-fabric:openclaw nc-fabric:openclaw-<commit>
```

The toolchain image is tagged `lucidlink-mcp-toolchain:<version>-<Dockerfile hash>`. It pins its base image by digest
and `lucidlink-mcp` by version, but not their dependencies. For a reproducible toolchain, build it once, push it to
your registry and use it by digest.

## Restore files

Service accounts can't create snapshots, but they can link the filespace's scheduled snapshots, which are read-only.
To copy a file back, run a spare daemon as `llagent` (`lucid daemon --instance <n>`), link it to a snapshot with
`lucid --instance <n> link --fs <filespace>.<workspace> --snapshot <id> --root-point <folder> --mount-point <dir>`,
copy the file into the live mount, then unlink and stop the spare instance.

## Teardown

* YAML: `nemoclaw destroy --state-dir .nemoclaw`, then remove the volumes that `prepare.sh`
  created: `docker volume ls -q --filter label=lucidlink.com/recipe=nemoclaw-v1-yaml | xargs -r docker volume rm`.
* OpenTofu: `tofu destroy -var destroy=true`.
* Host: `sudo systemctl disable --now agents-apply@<name> lucid-agent@<n>`, then remove the files that you no longer
  need from `/etc/lucid-agent`.
* LucidLink: delete the service accounts in the LucidLink web app. Files on the filespace stay.
