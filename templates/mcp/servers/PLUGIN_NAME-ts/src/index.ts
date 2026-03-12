import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "PLUGIN_NAME",
  version: "0.1.0",
});

// Replace this example tool with your own implementation.
server.tool(
  "example_tool",
  "An example tool — replace with your implementation.",
  { input: z.string().describe("Input string to echo back") },
  async ({ input }) => ({
    content: [{ type: "text", text: `You said: ${input}` }],
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
