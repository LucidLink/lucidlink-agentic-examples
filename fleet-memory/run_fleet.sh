#!/usr/bin/env bash
# Run the three agents in order and keep each one's output as run-<role>.log.
set -euo pipefail
cd "$(dirname "$0")"
for role in researcher analyst reviewer; do
    python3 fleet_agent.py "$role" | tee "run-$role.log"
done
