#!/usr/bin/env bash
# Launches the MCP server via tsx — installs deps on first run, cached thereafter.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [[ ! -d node_modules ]]; then
  npm install --silent
fi

exec npx tsx src/index.ts
