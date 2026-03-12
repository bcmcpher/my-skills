#!/bin/bash
# Launches the MCP server via uv — no pre-installed venv required.
# uv reads pyproject.toml and manages a cached virtualenv automatically.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/run_server.py"
