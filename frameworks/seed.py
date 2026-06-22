"""Seed a LucidLink filespace with the one file the snippets read.

Every snippet summarizes `/brief.md`. Drop in any markdown of your own at that
path, or just run this script to write a working default.

Run:  uv run --with lucidlink frameworks/seed.py
Env:  LUCIDLINK_TOKEN, LUCIDLINK_FILESPACE
"""

import os

import lucidlink

BRIEF = """# Brief

The Q2 marketing campaign launches our new collaborative video editing platform
for remote post-production teams. Goals: grow trial signups by 40%, highlight
real-time multi-user editing, and partner with three mid-size studios for
case-study content. The launch event is in early September, with a phased
rollout across email, paid social, and industry webinars.
"""

with lucidlink.Daemon() as daemon:
    workspace = daemon.authenticate(lucidlink.ServiceAccountCredentials(token=os.environ["LUCIDLINK_TOKEN"]))
    fs = workspace.link_filespace(name=os.environ["LUCIDLINK_FILESPACE"]).fs
    fs.write_file("/brief.md", BRIEF.encode())

print(f"Wrote /brief.md to '{os.environ['LUCIDLINK_FILESPACE']}'.")
