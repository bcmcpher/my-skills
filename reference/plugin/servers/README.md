# servers/

Bundled MCP server scripts for this plugin.

## When to create this directory

Create `servers/` only when your `.mcp.json` defines a local `stdio` server bundled
inside the plugin — e.g. a Python script that ships with the plugin rather than
being installed globally.

## How `.mcp.json` references it

`${CLAUDE_PLUGIN_ROOT}` expands to the plugin directory at runtime, so the path
resolves correctly regardless of where the plugin is installed.

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

---

## Option 1 — uv (default, recommended)

No virtualenv setup required. uv reads `pyproject.toml` and manages a cached
environment automatically.

**`servers/my-server/run.sh`** (chmod +x):
```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec uv run --project "$SCRIPT_DIR" python "$SCRIPT_DIR/run_server.py"
```

**`servers/my-server/run_server.py`**:
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def example_tool(input: str) -> str:
    """An example tool — replace with your implementation."""
    return f"You said: {input}"

if __name__ == "__main__":
    mcp.run()
```

**`servers/my-server/pyproject.toml`**:
```toml
[project]
name = "my-server"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.0",
]
```

---

## Option 2 — Docker (isolation, complex deps)

Use Docker when you need strict dependency isolation or have system-level dependencies.

**Build the image:**
```bash
docker build -t my-server-mcp servers/my-server/docker/
```

**`servers/my-server/docker/Dockerfile`**:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY run_server.py pyproject.toml ./

RUN pip install --no-cache-dir "mcp[cli]>=1.0"

CMD ["python", "run_server.py"]
```

**`servers/my-server/docker/run.sh`** (chmod +x):
```bash
#!/bin/bash
set -e
exec docker run --rm -i my-server-mcp
```

**Update `.mcp.json`** to point at the Docker launcher:
```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/my-server/docker/run.sh",
      "args": []
    }
  }
}
```

---

## When to delete this directory

Delete `servers/` (and remove the entry from `.mcp.json`) if:

- All your MCP servers are remote (`sse` or `http` type) — no local script needed.
- You are not using MCP at all.

Empty directories add no value; remove them before publishing the plugin.
