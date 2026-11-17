#!/usr/bin/env bash
# Run the shared-board showcase: both writers append N entries to one file at the same time, each entry under a
# LucidLink lock, then count. With locks, none is lost. The filespace audit trail shows each write under the
# writer's own service account.
#
#   cd examples/two-agents      (tofu workspace "showcase", applied with showcase.tfvars)
#   OPENSHELL_GATEWAY_ENDPOINT=http://127.0.0.1:17671 FILESPACE=my-filespace BOARD=/agents/shared/board.md \
#     ../../showcase/run.sh
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
: "${OPENSHELL_GATEWAY_ENDPOINT:?set the gateway endpoint}"; export OPENSHELL_GATEWAY_ENDPOINT
FILESPACE=${FILESPACE:?set FILESPACE to the filespace name}
BOARD=${BOARD:?set BOARD to the shared file on the filespace, e.g. /agents/shared/board.md}
N=${N:-5}
TOFU=${TOFU:-tofu}; OPENSHELL=${OPENSHELL:-openshell}
agents=$("$TOFU" output -json agents)
OPENSHELL_WORKSPACE=$(jq -r 'first(.[]).workspace' <<<"$agents"); export OPENSHELL_WORKSPACE

invoke() {  # sandbox prompt -> the agent's reply
  local rid; rid=$(jq -r --arg n "$1" '.[$n].runtime_id' <<<"$agents")
  jq -Rn --arg p "$2" '$p' | "$OPENSHELL" sandbox exec -n "$1" --no-tty -- \
    fabric-agent-ctl invoke --agent main --runtime-id "$rid" --input - | jq -r '.result.output.response // .result.error // .'
}
tool() {  # sandbox tool json-args -> the tool's text output (no LLM)
  "$OPENSHELL" sandbox exec -n "$1" --no-tty -- env LUCIDLINK_FILESPACE="$FILESPACE" \
    /opt/lucidlink/venv/bin/python - "$2" "$3" < "$HERE/../scripts/mcp-call.py"
}
task() {
  echo "Append $N entries to $BOARD, one entry at a time. For each entry: claim_file on $BOARD with blocking=true;" \
       "read_file; add the line '$1: entry <n>' at the end; write_file the whole content; release_file." \
       "Do not batch entries and never write without the claim. Reply with one line: how many entries you added."
}

echo "== reset $BOARD"
tool writer-a write_file "$(jq -nc --arg p "$BOARD" '{path: $p, content: "# Shared board\n\n"}')" >/dev/null

echo "== both writers at once ($N entries each)"
invoke writer-a "$(task writer-a)" > writer-a.out 2>&1 & a=$!
invoke writer-b "$(task writer-b)" > writer-b.out 2>&1 & b=$!
wait "$a" "$b" || true
echo "writer-a says: $(tail -1 writer-a.out)"; echo "writer-b says: $(tail -1 writer-b.out)"

echo "== count (read directly, no LLM)"
board=$(tool writer-a read_file "$(jq -nc --arg p "$BOARD" '{path: $p}')")
ca=$(grep -c '^writer-a: ' <<<"$board" || true); cb=$(grep -c '^writer-b: ' <<<"$board" || true)
echo "writer-a: $ca  writer-b: $cb  (expected $N each)"
echo "Who wrote what: the filespace audit trail (web app, or read_audit_trail with path_prefix=$BOARD)."
[ "$ca" = "$N" ] && [ "$cb" = "$N" ]
