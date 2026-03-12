from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PLUGIN_NAME")


@mcp.tool()
def example_tool(input: str) -> str:
    """An example tool — replace with your implementation."""
    return f"You said: {input}"


if __name__ == "__main__":
    mcp.run()
