"""One agent of the fleet. Run it once per role, each with its own service-account token:

  python fleet_agent.py researcher
  python fleet_agent.py analyst
  python fleet_agent.py reviewer

Each role reads its token from ~/.lucidlink/agent-<role>.token unless a path is given. The code is
the same for every role; only the token and the brief differ.

Env: LUCIDLINK_FILESPACE, ANTHROPIC_API_KEY; FLEET_MODEL picks another model ("provider:model").
"""

import argparse
import json
import os
import socket
from datetime import datetime, timezone

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langmem import create_manage_memory_tool, create_search_memory_tool
from lucidlink_store import LucidLinkStore, open_filespace

ROOT = "/memory"
SHARED = ("shared", "customers")
MODEL = os.environ.get("FLEET_MODEL", "anthropic:claude-haiku-4-5-20251001")

SYSTEM = (
    "You are one agent in a small fleet that shares memory through files on a LucidLink filespace. "
    "Use the memory tools for anything the fleet should remember. Keep memories short and factual."
)

BRIEFS = {
    "researcher": (
        "You are the researcher on the Acme pricing project. Notes from today's call with Acme: "
        "they renewed early; procurement wants a single annual invoice; their fiscal year ends in March. "
        "Store what the fleet should remember about Acme in shared memory, one fact per memory, "
        "then reply with the keys you wrote."
    ),
    "analyst": (
        "You are the pricing analyst on the Acme pricing project. First search shared memory for what "
        "the fleet already knows about Acme. Then record your proposal in shared memory as a decision: "
        "move Acme to the annual tier with a single invoice, pending review. Reply with what you found "
        "and the key you wrote."
    ),
    "reviewer": (
        "You are the reviewer, new to the Acme pricing project, starting from nothing. Search shared "
        "memory for what the fleet knows about Acme and who proposed the pricing decision. You cannot "
        "write to shared memory; write your review to your own private memory. Reply with a three-line "
        "summary naming which memories you relied on."
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("role", choices=BRIEFS)
    parser.add_argument("token_file", nargs="?", help="default: ~/.lucidlink/agent-<role>.token")
    args = parser.parse_args()

    client, filespace = open_filespace(args.token_file or f"~/.lucidlink/agent-{args.role}.token")
    try:
        store = LucidLinkStore(filespace, root=ROOT)
        tools = [
            create_search_memory_tool(namespace=SHARED, name="search_shared_memory"),
            create_manage_memory_tool(namespace=("agents", args.role), name="manage_private_memory"),
        ]
        if args.role != "reviewer":
            tools.append(create_manage_memory_tool(namespace=SHARED, name="manage_shared_memory"))
        agent = create_agent(init_chat_model(MODEL, temperature=0), tools, system_prompt=SYSTEM, store=store)

        stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{stamp}] {args.role} on {socket.gethostname()} — filespace {filespace.name}, root {ROOT}")
        result = agent.invoke({"messages": [{"role": "user", "content": BRIEFS[args.role]}]})
        for message in result["messages"]:
            if message.type == "ai" and message.tool_calls:
                for call in message.tool_calls:
                    shown = {k: v if len(json.dumps(v)) < 160 else "…" for k, v in call["args"].items()}
                    print(f"  tool  {call['name']}({json.dumps(shown, ensure_ascii=False)})")
            elif message.type == "tool":
                print(f"  ->    {str(message.content)[:140]}")
        print(f"\n{args.role} says:\n{result['messages'][-1].content}\n")
    finally:
        client.close()


if __name__ == "__main__":
    main()
