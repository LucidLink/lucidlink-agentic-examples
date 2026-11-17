#!/usr/bin/env bash
# Boot-time apply for one agent deployment (run by agents-apply@<name>.service).
#
# Applies in-place changes only, such as restarting agent runtimes that didn't survive the reboot. A plan that would
# delete or replace something is re-checked for a few minutes (right after boot, a sandbox the gateway is still
# restarting can look replaceable); if it persists, the script exits 2 and leaves it for a person to review. Other
# failures exit 1, and the unit retries them.
#
# Settings (from /etc/lucid-agent/apply-<name>.env):
#   MODE=tofu      WORKDIR=<OpenTofu example dir>  TOFU=<tofu binary>  TF_CLI_CONFIG_FILE=...
#                  (+ TF_WORKSPACE=<workspace> and TF_CLI_ARGS_plan=-var-file=<file> for a non-default workspace)
#   MODE=nemoclaw  WORKDIR=<dir>  NEMOCLAW=<nemoclaw binary>  NEMOCLAW_CONFIG=<yaml>  NEMOCLAW_STATE_DIR=<dir>
#   plus the model API keys: NVIDIA_API_KEY and ANTHROPIC_API_KEY.
#   RISKY_RETRIES (default 6) and RISKY_WAIT (seconds, default 30) bound the re-checks.
set -euo pipefail
cd "${WORKDIR:?set WORKDIR}"
RETRIES=${RISKY_RETRIES:-6}; WAIT=${RISKY_WAIT:-30}
refuse() { printf 'agents: refusing unattended apply; the plan deletes or replaces:\n%s\nApply by hand.\n' "$1" >&2; exit 2; }

case "${MODE:-tofu}" in
tofu)
  TOFU=${TOFU:-tofu}
  plan=$(mktemp); trap 'rm -f "$plan"' EXIT
  for ((try = 1; ; try++)); do
    set +e; "$TOFU" plan -input=false -no-color -detailed-exitcode -out="$plan"; rc=$?; set -e
    case $rc in 0) echo "agents: no changes"; exit 0 ;; 2) ;; *) exit 1 ;; esac
    risky=$("$TOFU" show -json "$plan" | jq -r '(.resource_changes // [])[] | select(.change.actions | index("delete")) | .address')
    [ -n "$risky" ] || break
    [ "$try" -lt "$RETRIES" ] || refuse "$risky"
    echo "agents: plan replaces resources; re-checking in ${WAIT}s ($try/$RETRIES)"; sleep "$WAIT"
  done
  "$TOFU" apply -input=false -no-color "$plan"     # applies exactly the checked plan
  ;;
nemoclaw)
  NEMOCLAW=${NEMOCLAW:-nemoclaw}
  args=(--progress off --non-interactive --state-dir "${NEMOCLAW_STATE_DIR:?}" "${NEMOCLAW_CONFIG:?}")
  changes() {  # sorted change list as JSON; exit 1 if the plan fails or its shape is unexpected
    local json; json=$("$NEMOCLAW" plan -o json "${args[@]}") || return 1
    jq -e '.changes | type == "array"' <<<"$json" >/dev/null || { echo "agents: unexpected plan output" >&2; return 1; }
    jq -cS '[.changes[] | {resource, actions}] | sort_by(.resource)' <<<"$json"
  }
  for ((try = 1; ; try++)); do
    first=$(changes) || exit 1
    [ "$first" != "[]" ] || { echo "agents: no changes"; exit 0; }
    risky=$(jq -r '.[] | select(.actions | index("delete")) | .resource' <<<"$first")
    if [ -n "$risky" ]; then
      [ "$try" -lt "$RETRIES" ] || refuse "$risky"
      echo "agents: plan replaces resources; re-checking in ${WAIT}s ($try/$RETRIES)"; sleep "$WAIT"; continue
    fi
    # NemoClaw has no saved-plan apply: `apply` plans again. Require the config to be unchanged and a second plan,
    # taken a little later, to match the first, so a state that is still settling isn't applied. A change between
    # this check and apply's own plan remains possible; the window is seconds.
    sum=$(sha256sum "$NEMOCLAW_CONFIG")
    sleep "${SETTLE:-20}"
    second=$(changes) || exit 1
    [ "$second" = "$first" ] && [ "$(sha256sum "$NEMOCLAW_CONFIG")" = "$sum" ] && break
    echo "agents: plan changed between checks; re-checking ($try/$RETRIES)"
    [ "$try" -lt "$RETRIES" ] || exit 1
  done
  jq -r '.[] | "agents: \(.actions | join(",")) \(.resource)"' <<<"$first"
  "$NEMOCLAW" apply "${args[@]}"
  ;;
*) echo "MODE must be tofu or nemoclaw" >&2; exit 2 ;;
esac
