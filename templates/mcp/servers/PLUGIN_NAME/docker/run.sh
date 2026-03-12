#!/bin/bash
# Alternative launcher: run the MCP server in Docker.
# Build first: docker build -t PLUGIN_NAME-mcp servers/PLUGIN_NAME/docker/
# Then in .mcp.json set:
#   "command": "${CLAUDE_PLUGIN_ROOT}/servers/PLUGIN_NAME/docker/run.sh"
set -e
exec docker run --rm -i PLUGIN_NAME-mcp
