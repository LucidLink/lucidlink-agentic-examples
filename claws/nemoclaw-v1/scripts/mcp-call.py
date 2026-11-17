"""Call one LucidLink MCP tool from inside a sandbox, without an LLM (used by verify.sh and showcase/run.sh).

Runs with the toolchain's Python (the only program allowed to reach LucidLink) and starts the sandbox's own MCP
server over stdio:  python - <tool> '<json arguments>'  (script on stdin). Prints the tool's text result.
"""

import json
import subprocess
import sys

tool, arguments = sys.argv[1], json.loads(sys.argv[2])
server = subprocess.Popen(
    ["/opt/lucidlink/bin/lucidlink-mcp-launch"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
)


def send(message):
    server.stdin.write(json.dumps(message) + "\n")
    server.stdin.flush()


def receive(request_id):
    for line in server.stdout:
        message = json.loads(line)
        if message.get("id") == request_id:
            return message
    raise SystemExit("MCP server exited")


send(
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "showcase", "version": "1"},
        },
    }
)
receive(1)
send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": tool, "arguments": arguments}})
result = receive(2).get("result", {})
server.terminate()
print("".join(part.get("text", "") for part in result.get("content", [])))
sys.exit(1 if result.get("isError") else 0)
