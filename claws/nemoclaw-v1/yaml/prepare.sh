#!/usr/bin/env bash
# Prepare the LucidLink volumes for a NemoClaw v1 deployment and render its YAML.
#
#   ./prepare.sh [lucidlink.env]
#   NVIDIA_API_KEY=... ANTHROPIC_API_KEY=... nemoclaw apply --state-dir .nemoclaw lucidlink-agents.yaml
#
# Run as a user that can use Docker, after host/install-host.sh. Safe to re-run: it builds the toolchain image if
# missing, fills the toolchain volume once and creates each volume once. Volume names include a hash of their
# source, so a changed source gets a new volume (Docker volumes can't be changed). No secret passes through here:
# the credential volumes only bind the token directories.
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
ROOT=$(cd "$HERE/.." && pwd)
ENV_FILE=${1:-$HERE/lucidlink.env}
[ -f "$ENV_FILE" ] || { echo "no $ENV_FILE (copy lucidlink.env.example)" >&2; exit 2; }

# First run: give the deployment a stable identity.
if ! grep -qE '^NEMOCLAW_UID=.+' "$ENV_FILE"; then
  uid=$( (uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid) | tr 'A-Z' 'a-z')
  if grep -q '^NEMOCLAW_UID=' "$ENV_FILE"; then sed -i.bak "s/^NEMOCLAW_UID=.*/NEMOCLAW_UID=$uid/" "$ENV_FILE" && rm -f "$ENV_FILE.bak"
  else echo "NEMOCLAW_UID=$uid" >> "$ENV_FILE"; fi
  echo "new deployment uid $uid written to $ENV_FILE"
fi

set -a; . "$ENV_FILE"; set +a
for v in NEMOCLAW_UID DEPLOYMENT_NAME GATEWAY_PORT GATEWAY_CIDR FILESPACE_NAME FILESPACE_ID STORAGE_HOST \
         RESEARCHER_CRED_DIR CODER_CRED_DIR SKILLS_DIR CODER_DIR OPENCLAW_IMAGE CLAUDE_IMAGE \
         RESEARCHER_PROVIDER RESEARCHER_MODEL CODER_MODEL LUCIDLINK_MCP_VERSION; do
  [ -n "${!v:-}" ] || { echo "$v is not set in $ENV_FILE" >&2; exit 2; }
done
BUCKET=${BUCKET:-lucid-fs-$FILESPACE_ID}
INTERPRETER=${INTERPRETER:-/opt/lucidlink/python/cpython-3.12.16-linux-x86_64-gnu/bin/python3.12}
# Values go into YAML unescaped, so allow only plain characters (and catch unfilled placeholders).
for v in NEMOCLAW_UID DEPLOYMENT_NAME GATEWAY_PORT GATEWAY_CIDR FILESPACE_NAME FILESPACE_ID STORAGE_HOST BUCKET \
         OPENCLAW_IMAGE CLAUDE_IMAGE RESEARCHER_MODEL CODER_MODEL INTERPRETER; do
  [[ ${!v} =~ ^[A-Za-z0-9._:/@+-]+$ ]] || { echo "$v has unexpected characters: '${!v}'" >&2; exit 2; }
done
[[ $FILESPACE_ID =~ ^[0-9a-f-]{36}$ && $FILESPACE_ID != 00000000-0000-0000-0000-000000000000 ]] \
  || { echo "set FILESPACE_ID (lucid status: Filespace id)" >&2; exit 2; }
[[ $RESEARCHER_PROVIDER == nvidia || $RESEARCHER_PROVIDER == anthropic ]] \
  || { echo "RESEARCHER_PROVIDER must be nvidia or anthropic" >&2; exit 2; }
[[ $OPENCLAW_IMAGE == *@sha256:* && $CLAUDE_IMAGE == *@sha256:* ]] || { echo "pin OPENCLAW_IMAGE/CLAUDE_IMAGE by digest" >&2; exit 2; }
WORKSPACE=nc-$(printf '%s' "$NEMOCLAW_UID" | sha256sum | cut -c1-16)
# Volume names carry part of the workspace hash, so two deployments (or the OpenTofu flavour) never share one.
PREFIX=${PREFIX:-$DEPLOYMENT_NAME-${WORKSPACE:3:6}}
OUT=${OUT:-$HERE/lucidlink-agents.yaml}
short() { printf '%s' "$1" | sha1sum | cut -c1-8; }
LABELS=(--label openshell.ai/sandbox-attachable=true
        --label "openshell.ai/sandbox-attachable-workspace=$WORKSPACE"
        --label lucidlink.com/recipe=nemoclaw-v1-yaml)

# -- toolchain: image tagged by version + Dockerfile hash, volume named after the tag
TAG="lucidlink-mcp-toolchain:$LUCIDLINK_MCP_VERSION-$(sha1sum "$ROOT/toolchain/Dockerfile" | cut -c1-8)"
if ! docker image inspect "$TAG" >/dev/null 2>&1; then
  echo "building $TAG"
  docker build -q --build-arg "LUCIDLINK_MCP_VERSION=$LUCIDLINK_MCP_VERSION" -t "$TAG" "$ROOT/toolchain" >/dev/null
fi
TOOLCHAIN_VOL="$PREFIX-toolchain-$(short "$TAG")"
check_label() {  # name: an existing volume must be labelled for this deployment's workspace
  local have; have=$(docker volume inspect -f '{{index .Labels "openshell.ai/sandbox-attachable-workspace"}}' "$1")
  [ "$have" = "$WORKSPACE" ] || { echo "volume $1 is labelled for workspace '$have', not $WORKSPACE" >&2; exit 1; }
}
if docker volume inspect "$TOOLCHAIN_VOL" >/dev/null 2>&1; then check_label "$TOOLCHAIN_VOL"
else docker volume create "${LABELS[@]}" "$TOOLCHAIN_VOL" >/dev/null; fi
docker run --rm --network none --user 0:0 --entrypoint /bin/sh -v "$TOOLCHAIN_VOL:/dst" "$TAG" -c '
  set -eu; want="$1"; have=$(cat /opt/lucidlink/INTERPRETER)
  [ "$have" = "$want" ] || { echo "image interpreter $have != INTERPRETER $want" >&2; exit 3; }
  if [ "$(cat /dst/INTERPRETER 2>/dev/null || true)" = "$want" ] && [ -x /dst/bin/lucidlink-mcp-launch ]; then exit 0; fi
  rm -rf /dst/* && cp -a /opt/lucidlink/. /dst/ && test -x /dst/bin/lucidlink-mcp-launch && echo "toolchain copied"
' sh "$INTERPRETER"

# -- bind-backed volumes: token directories and LucidLink folders
bind_volume() {  # name source
  local name=$1 src=$2 have
  [ -d "$src" ] || { echo "$src does not exist (or isn't visible to $(id -un)); run host/install-host.sh first" >&2; exit 1; }
  if have=$(docker volume inspect -f '{{index .Options "device"}}' "$name" 2>/dev/null); then
    [ "$have" = "$src" ] || { echo "volume $name binds $have, not $src" >&2; exit 1; }
    check_label "$name"
  else
    docker volume create -d local -o type=none -o o=bind -o "device=$src" "${LABELS[@]}" "$name" >/dev/null
  fi
  echo "$name"
}
RESEARCHER_CRED_VOL=$(bind_volume "$PREFIX-cred-researcher-$(short "$RESEARCHER_CRED_DIR")" "$RESEARCHER_CRED_DIR")
CODER_CRED_VOL=$(bind_volume "$PREFIX-cred-coder-$(short "$CODER_CRED_DIR")" "$CODER_CRED_DIR")
SKILLS_VOL=$(bind_volume "$PREFIX-dir-skills-$(short "$SKILLS_DIR")" "$SKILLS_DIR")
CODER_VOL=$(bind_volume "$PREFIX-dir-coder-$(short "$CODER_DIR")" "$CODER_DIR")

# -- render
export WORKSPACE BUCKET INTERPRETER TOOLCHAIN_VOL RESEARCHER_CRED_VOL CODER_CRED_VOL SKILLS_VOL CODER_VOL
VARS='$WORKSPACE $DEPLOYMENT_NAME $NEMOCLAW_UID $GATEWAY_PORT $GATEWAY_CIDR $FILESPACE_NAME $FILESPACE_ID
      $STORAGE_HOST $BUCKET $INTERPRETER $OPENCLAW_IMAGE $CLAUDE_IMAGE
      $RESEARCHER_PROVIDER $RESEARCHER_MODEL $CODER_MODEL
      $TOOLCHAIN_VOL $RESEARCHER_CRED_VOL $CODER_CRED_VOL $SKILLS_VOL $CODER_VOL'
envsubst "$VARS" < "$HERE/lucidlink-agents.yaml.tmpl" > "$OUT"

echo "workspace $WORKSPACE; rendered $OUT"
used=" $TOOLCHAIN_VOL $RESEARCHER_CRED_VOL $CODER_CRED_VOL $SKILLS_VOL $CODER_VOL "
stale=$(docker volume ls -q --filter label=lucidlink.com/recipe=nemoclaw-v1-yaml \
          --filter "label=openshell.ai/sandbox-attachable-workspace=$WORKSPACE" | while read -r v; do
          [[ $used == *" $v "* ]] || echo "$v"; done)
[ -z "$stale" ] || printf 'no longer used (remove after the next apply): docker volume rm %s\n' "$(echo $stale)"
keys=ANTHROPIC_API_KEY; [ "$RESEARCHER_PROVIDER" = nvidia ] && keys="NVIDIA_API_KEY=... $keys"
echo "next: $keys=... nemoclaw apply --state-dir $HERE/.nemoclaw $OUT   (keep that state directory)"
