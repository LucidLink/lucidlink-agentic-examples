# Get NemoClaw v1

NemoClaw v1 has no release yet, so you build the bundle (the `nemoclaw` CLI, OpenTofu and the providers) and the
agent images from source. NemoClaw's [build guide](https://github.com/NVIDIA/NemoClaw/blob/v1/docs/build-deploy/build.md)
is the reference. These steps were tested on Ubuntu 24.04 x86_64 with 4 vCPUs, 16 GB of memory and 150 GB of disk.
The bundle takes about 25 minutes to build, and each image about 6 minutes.

1. Install the build tools and Docker:

   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential pkg-config git jq unzip uuid-runtime gettext-base docker.io docker-buildx
   sudo usermod -aG docker "$USER"     # then sign in again
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain none
   . ~/.cargo/env
   ```

2. Check out the tested commit:

   ```bash
   git clone https://github.com/NVIDIA/NemoClaw.git && cd NemoClaw
   git checkout ce910d0     # the tested commit
   ```

3. Build the bundle and copy it to a fixed location:

   ```bash
   cargo ci tools
   export PROTOC=$PWD/.tools/protoc-36.2/bin/protoc
   cargo run -p nemoclaw-build -- bundle
   cp -a dist/linux_amd64 ~/nemoclaw-bundle
   export PATH=~/nemoclaw-bundle/bin:$PATH
   nemoclaw --help
   ```

4. Build the OpenClaw and Claude images, and tag each with the commit at once. The build always tags
   `nc-fabric:<harness>`, so a later build moves that tag:

   ```bash
   commit=$(git rev-parse --short HEAD)
   for h in openclaw claude; do
     cargo images build --platform linux/amd64 "$h"
     docker tag "nc-fabric:$h" "nc-fabric:$h-$commit"
     docker image inspect "nc-fabric:$h" --format '{{index .RepoDigests 0}}'
   done
   ```

   Use the printed `nc-fabric@sha256:…` references as the image digests in this example.

5. Install the OpenShell CLI version that `versions.json` names, and check its SHA-256 against the value there:

   ```bash
   v=$(jq -r .openshell versions.json)
   url=$(jq -r .platforms.linux_amd64.openshell.url versions.json)
   sum=$(jq -r .platforms.linux_amd64.openshell.sha256 versions.json)
   curl -fsSLo /tmp/openshell.tgz "$url" && echo "$sum  /tmp/openshell.tgz" | sha256sum -c
   sudo tar -xzf /tmp/openshell.tgz -C /usr/local/bin openshell && openshell --version   # expect $v
   ```

6. For the OpenTofu path, point OpenTofu at the bundle's providers:

   ```bash
   cat > ~/nemoclaw-bundle/providers.tfrc <<EOF
   provider_installation {
     filesystem_mirror { path = "$HOME/nemoclaw-bundle/providers" }
   }
   EOF
   ```

   Use `~/nemoclaw-bundle/libexec/tofu` as `tofu`, and `~/nemoclaw-bundle/providers.tfrc` as `TF_CLI_CONFIG_FILE`.
