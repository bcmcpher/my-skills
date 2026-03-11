# servers/

Bundled MCP server binaries or scripts for this plugin.

## When to create this directory

Create `servers/` only when your `.mcp.json` defines a local `stdio` server that is
bundled inside the plugin — for example a compiled binary or a small Node/Python script
that ships with the plugin rather than being installed globally.

## How `.mcp.json` references it

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server/run.sh",
      "args": []
    }
  }
}
```

`${CLAUDE_PLUGIN_ROOT}` expands to the plugin directory at runtime, so the path resolves
correctly regardless of where the plugin is installed.

## When to delete this directory

Delete `servers/` (and remove the corresponding entry from `.mcp.json`) if:

- All your MCP servers are remote (`sse` or `http` type) — no local binary needed.
- You are not using MCP at all.

Empty directories add no value; remove them before publishing the plugin.
