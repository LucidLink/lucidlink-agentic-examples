#!/usr/bin/env bash
# Check a deployment of this example from the host. Each check prints "ok <check>" or "FAIL <check>: <detail>";
# the script exits 1 if any check fails. Without RESEARCHER_RUNTIME, no check uses a model.
#
#   OPENSHELL_GATEWAY_ENDPOINT=http://127.0.0.1:17671 OPENSHELL_WORKSPACE=<workspace> \
#   FILESPACE=<filespace> SKILLS_PATH=/agents/team-skills CODER_PATH=/agents/coder \
#     scripts/verify.sh
#
# The workspace and the runtime IDs are in the output of `nemoclaw apply` (YAML) or `tofu output agents` (OpenTofu).
#   RESEARCHER_RUNTIME=<runtime id>  also ask the researcher, through its model, to list SKILLS_PATH with its tools
#   RESEARCHER=researcher CODER=coder  sandbox names, if you changed them
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
: "${OPENSHELL_GATEWAY_ENDPOINT:?}" "${OPENSHELL_WORKSPACE:?}" "${FILESPACE:?}" "${SKILLS_PATH:?}" "${CODER_PATH:?}"
export OPENSHELL_GATEWAY_ENDPOINT OPENSHELL_WORKSPACE
OPENSHELL=${OPENSHELL:-openshell}
RESEARCHER=${RESEARCHER:-researcher}
CODER=${CODER:-coder}
failed=0

ok() { echo "ok   $1"; }
fail() { echo "FAIL $1: $2"; failed=1; }
run() { "$OPENSHELL" sandbox exec -n "$1" --no-tty -- "${@:2}" 2>&1; }
tool() {  # sandbox tool json-arguments: call one LucidLink MCP tool in the sandbox, without a model
  "$OPENSHELL" sandbox exec -n "$1" --no-tty -- env LUCIDLINK_FILESPACE="$FILESPACE" \
    /opt/lucidlink/venv/bin/python - "$2" "$3" < "$HERE/mcp-call.py" 2>&1
}
probe=".verify-$(date +%s)-$$"

echo "== $RESEARCHER"
out=$(run "$RESEARCHER" ls -A /sandbox/skills) && [ -n "$out" ] \
  && ok "team skills are visible at /sandbox/skills ($(wc -l <<<"$out" | tr -d ' ') entries)" \
  || fail "team skills at /sandbox/skills" "${out:-empty}"
out=$(run "$RESEARCHER" touch "/sandbox/skills/$probe")
[[ $out == *"Read-only file system"* ]] && ok "/sandbox/skills refuses writes" || fail "/sandbox/skills refuses writes" "$out"
out=$(tool "$RESEARCHER" list_files "$(jq -nc --arg p "$SKILLS_PATH" '{path: $p}')") \
  && ok "MCP list_files $SKILLS_PATH" || fail "MCP list_files $SKILLS_PATH" "$out"
skills=$out
out=$(tool "$RESEARCHER" write_file "$(jq -nc --arg p "$SKILLS_PATH/$probe" '{path: $p, content: "x"}')")
[[ $out == *"Authorization exception"* ]] && ok "the researcher's account can't write (Authorization exception)" \
  || fail "the researcher's account can't write" "$out"

echo "== $CODER"
out=$(run "$CODER" sh -c "printf '%s' '$probe' > /sandbox/workspace/$probe && cat /sandbox/workspace/$probe")
[ "$out" = "$probe" ] && ok "/sandbox/workspace is writable" || fail "/sandbox/workspace is writable" "$out"
out=$(tool "$CODER" read_file "$(jq -nc --arg p "$CODER_PATH/$probe" '{path: $p}')")
[ $? = 0 ] && [ "$(tail -n 1 <<<"$out")" = "$probe" ] && ok "the file is on the filespace at $CODER_PATH (read with MCP)" \
  || fail "the file is on the filespace at $CODER_PATH" "$out"
run "$CODER" rm -f "/sandbox/workspace/$probe" >/dev/null
out=$(run "$CODER" python3 -c '
import urllib.request
try:
    urllib.request.urlopen("https://api.lucidlink.com/", timeout=10)
    print("reached")
except Exception as e:
    print(e)')
[[ $out != reached* ]] && ok "other programs can't reach LucidLink ($out)" || fail "egress policy" "python3 reached api.lucidlink.com"

if [ -n "${RESEARCHER_RUNTIME:-}" ]; then
  echo "== $RESEARCHER, through its model"
  name=$(awk '/^ +(DIR|FILE) /{print $NF; exit}' <<<"$skills")
  reply=$(jq -Rn --arg p "Use your LucidLink list_files tool on $SKILLS_PATH and reply with the entry names, one per line." '$p' \
    | "$OPENSHELL" sandbox exec -n "$RESEARCHER" --no-tty -- fabric-agent-ctl invoke --agent main \
        --runtime-id "$RESEARCHER_RUNTIME" --input - 2>&1 | jq -r '.result.output.response // .result.error // .' 2>&1)
  [ -n "$name" ] && [[ $reply == *"$name"* ]] && ok "the researcher lists $SKILLS_PATH (found $name)" \
    || fail "the researcher lists $SKILLS_PATH" "$(head -c 300 <<<"$reply")"
fi

exit $failed
