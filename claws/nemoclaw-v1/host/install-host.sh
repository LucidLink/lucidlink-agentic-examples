#!/usr/bin/env bash
# Host side of LucidLink for NemoClaw v1 (Linux, run with sudo). Idempotent.
#
#   install-host.sh base
#       llagent user (uid/gid = sandbox uid, 10001), fuse allow_other, lucid-agent@ unit.
#   install-host.sh mount [--force] <instance> <filespace.workspace> <root-point> <mount-point>   < token
#       A LucidLink daemon instance as llagent, mounting <root-point> at <mount-point> before Docker starts.
#       Files appear owned by 10001, so sandboxes can write without chmod 777. Mount read-only folders with
#       a read-only service account, so LucidLink itself refuses writes. Re-running with the same settings and
#       token does nothing; changing a running instance needs --force, after stopping the sandboxes using it.
#   install-host.sh mcp-token <name>   < token
#       /etc/lucid-agent/mcp-<name>/token for the in-sandbox MCP server (owned by the sandbox uid, 0400).
#
# Tokens are only read from stdin and written 0600/0400; they never appear in argv or logs.
# Don't stop an instance while sandboxes use its mount (the daemon stops responding): stop those sandbox
# containers first, then restart the unit, then apply again.
set -euo pipefail

AGENT_UID=${AGENT_UID:-10001}
AGENT_USER=${AGENT_USER:-llagent}
CONF=/etc/lucid-agent
HERE=$(cd "$(dirname "$0")" && pwd)

need_root() { [ "$(id -u)" = 0 ] || { echo "run with sudo" >&2; exit 1; }; }
read_token() {
  [ -t 0 ] && { echo "pipe the token on stdin" >&2; exit 1; }
  local t; t=$(cat); [ -n "$t" ] || { echo "empty token" >&2; exit 1; }
  printf '%s\n' "$t"
}

abs_path() { [[ $1 == /* && $1 != *$'\n'* && $1 != *' '* ]] || { echo "$2 must be an absolute path without spaces: $1" >&2; exit 2; }; }

cmd_base() {
  command -v lucid >/dev/null || { echo "install the LucidLink client (.deb) first" >&2; exit 1; }
  command -v fusermount3 >/dev/null || { echo "install fuse3 first" >&2; exit 1; }
  local by_uid by_name
  by_uid=$(getent passwd "$AGENT_UID" | cut -d: -f1 || true)
  by_name=$(getent passwd "$AGENT_USER" | cut -d: -f3 || true)
  if [ -z "$by_uid" ] && [ -z "$by_name" ]; then
    getent group "$AGENT_UID" >/dev/null || groupadd -g "$AGENT_UID" "$AGENT_USER"
    useradd -u "$AGENT_UID" -g "$AGENT_UID" -m -s /usr/sbin/nologin "$AGENT_USER"
  elif [ "$by_uid" != "$AGENT_USER" ] || [ "$by_name" != "$AGENT_UID" ]; then
    echo "uid $AGENT_UID is '${by_uid:-none}' and user $AGENT_USER has uid '${by_name:-none}'; set AGENT_USER/AGENT_UID to match" >&2
    exit 1
  fi
  grep -q '^user_allow_other' /etc/fuse.conf || echo user_allow_other >> /etc/fuse.conf
  install -d -m 0755 "$CONF"
  sed "s#/usr/local/bin/lucid#$(command -v lucid)#g; s#^User=.*#User=$AGENT_USER#; s#^Group=.*#Group=$AGENT_USER#" \
    "$HERE/lucid-agent@.service" > /etc/systemd/system/lucid-agent@.service
  systemctl daemon-reload
  echo "base ok: $(id "$AGENT_USER")"
}

cmd_mount() {
  local force=0; [ "${1:-}" = --force ] && { force=1; shift; }
  [ $# -eq 4 ] || { echo "usage: mount [--force] <instance> <filespace.workspace> <root-point> <mount-point>" >&2; exit 2; }
  local inst=$1 fs=$2 root=$3 mp=$4
  [[ $inst =~ ^[0-9]+$ ]] || { echo "instance must be a number" >&2; exit 2; }
  [[ $fs =~ ^[A-Za-z0-9._-]+$ ]] || { echo "filespace must look like <filespace>.<workspace>" >&2; exit 2; }
  abs_path "$root" root-point; abs_path "$mp" mount-point
  local tok; tok=$(read_token)
  local env; env=$(printf 'LUCID_FS=%s\nLUCID_ROOT_POINT=%s\nLUCID_MOUNT_POINT=%s' "$fs" "$root" "$mp")
  if systemctl is-active -q "lucid-agent@$inst"; then
    if [ "$(cat "$CONF/$inst.env" 2>/dev/null)" = "$env" ] && [ "$(cat "$CONF/$inst.token" 2>/dev/null)" = "$tok" ]; then
      echo "unchanged: lucid-agent@$inst"; return 0
    fi
    [ $force = 1 ] || { echo "lucid-agent@$inst is running with other settings. Stop the sandbox containers that use $mp, then re-run with --force." >&2; exit 1; }
  fi
  mountpoint -q "$mp" || install -d -o "$AGENT_USER" -g "$AGENT_USER" -m 0750 "$mp"
  printf '%s\n' "$env" > "$CONF/$inst.env"
  ( umask 077; printf '%s\n' "$tok" > "$CONF/$inst.token" ); chown root:root "$CONF/$inst.token"; chmod 0600 "$CONF/$inst.token"
  systemctl enable "lucid-agent@$inst" >/dev/null
  systemctl restart "lucid-agent@$inst"
  if mountpoint -q "$mp"; then echo "mount ok: $mp ($(stat -c %u:%g "$mp"))"
  else echo "lucid-agent@$inst started but $mp is not mounted; see journalctl -u lucid-agent@$inst" >&2; exit 1; fi
}

cmd_mcp_token() {
  [ $# -eq 1 ] && [[ $1 =~ ^[a-z0-9-]+$ ]] || { echo "usage: mcp-token <name>" >&2; exit 2; }
  local d="$CONF/mcp-$1" tok; tok=$(read_token)
  install -d -o "$AGENT_UID" -g "$AGENT_UID" -m 0500 "$d"
  ( umask 077; printf '%s\n' "$tok" > "$d/token.new" ); chown "$AGENT_UID:$AGENT_UID" "$d/token.new"; chmod 0400 "$d/token.new"
  mv -f "$d/token.new" "$d/token"
  echo "mcp token ok: $d"
}

need_root
case "${1:-}" in
  base) shift; cmd_base "$@" ;;
  mount) shift; cmd_mount "$@" ;;
  mcp-token) shift; cmd_mcp_token "$@" ;;
  *) sed -n '2,22p' "$0"; exit 2 ;;
esac
