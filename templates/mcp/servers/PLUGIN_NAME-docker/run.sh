#!/usr/bin/env bash
# Launches the MCP server in Docker (stdio transport).
# Builds the image on first run; skips rebuild if already present.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="mcp-PLUGIN_NAME"

if ! docker image inspect "$IMAGE" &>/dev/null; then
  echo "[mcp-PLUGIN_NAME] Building Docker image..." >&2
  docker build -t "$IMAGE" "$SCRIPT_DIR" >&2
fi

exec docker run --rm -i "$IMAGE"
