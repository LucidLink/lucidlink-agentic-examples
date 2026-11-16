# LucidLink MCP toolchain: a self-contained Python + lucidlink-mcp under /opt/lucidlink.
# The module copies /opt/lucidlink into a Docker volume that any NemoClaw sandbox image
# mounts read-only, so stock nc-fabric images need no rebuild. Any glibc image can use it.
# Base pinned by digest; lucidlink-mcp pinned by version (its dependencies are not hash-locked).
FROM debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc
COPY --from=ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 /uv /usr/local/bin/uv
ARG PYTHON_VERSION=3.12.16
ARG LUCIDLINK_MCP_VERSION=1.0.1
ENV UV_PYTHON_INSTALL_DIR=/opt/lucidlink/python UV_NO_CACHE=1
RUN uv python install "${PYTHON_VERSION}" \
 && uv venv --python "${PYTHON_VERSION}" /opt/lucidlink/venv \
 && uv pip install --python /opt/lucidlink/venv/bin/python "lucidlink-mcp==${LUCIDLINK_MCP_VERSION}" \
 && mkdir -p /opt/lucidlink/bin \
 && printf '#!/bin/sh\n# Reads the token from the read-only secret volume; never from the agent config.\n[ -s /etc/lucidlink/token ] || { echo "lucidlink-mcp: /etc/lucidlink/token missing or empty" >&2; exit 1; }\nLUCIDLINK_TOKEN="$(cat /etc/lucidlink/token)" HOME=/tmp\nexport LUCIDLINK_TOKEN HOME\nexec /opt/lucidlink/venv/bin/lucidlink-mcp "$@"\n' > /opt/lucidlink/bin/lucidlink-mcp-launch \
 && chmod -R a+rX /opt/lucidlink && chmod 755 /opt/lucidlink/bin/lucidlink-mcp-launch \
 && /opt/lucidlink/venv/bin/python -c "import lucidlink, lucidlink_mcp" \
 && readlink -f /opt/lucidlink/venv/bin/python > /opt/lucidlink/INTERPRETER && cat /opt/lucidlink/INTERPRETER
