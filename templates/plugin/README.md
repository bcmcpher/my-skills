# Full Plugin Template

Copy this directory to `plugins/my-plugin-name`, then:

1. Rename `skills/SKILL_NAME/` and `agents/AGENT_NAME/` directories
2. Edit `.claude-plugin/plugin.json` — update all placeholder values
3. Edit the `SKILL.md` files — fill in frontmatter and bodies
4. Edit `hooks/hooks.json` — configure your hooks (or delete if not needed)
5. Edit `.mcp.json` — configure MCP servers (or delete if not needed)
6. Test: `claude --plugin-dir ./plugins/my-plugin-name`

---

## Step-by-step process

### 1. Rename placeholders

```bash
mv plugins/my-plugin-name/skills/SKILL_NAME  plugins/my-plugin-name/skills/your-skill
mv plugins/my-plugin-name/agents/AGENT_NAME  plugins/my-plugin-name/agents/your-agent
```

Update the `skills` and `agents` arrays in `plugin.json` to match the new paths.

### 2. Write the skill

**`name`** becomes the slash command. Keep it short and typed-friendly.

**`description`** is the auto-invocation trigger — the condition under which Claude runs this skill automatically. Be specific: *what situation triggers it, what does it produce?*

Write the body as imperative steps + constraints. Reference `$ARGUMENTS` if the skill takes user input.

### 3. Write the agent

**`description`** is a delegation trigger — it tells the main Claude *when* to hand off to this agent. Describe the condition, not the agent's personality.

- Good: `"Delegate when the user asks for a detailed security audit of a file or function"`
- Bad: `"A security-focused assistant"`

The body of the agent's `SKILL.md` is its system prompt. Start with a purpose statement, list explicit steps, end with `Always:` / `Never:` constraints.

### 4. Decide what to include

**Start with just a skill or just an agent.** Add the rest only when you have a concrete need:

- **Hooks** — for side effects: logging tool calls, linting output, blocking dangerous operations. Don't add hooks by default; they run on every matching event and can slow things down.
- **MCP servers** — for external data or filesystem access beyond what Claude's built-in tools provide. Only needed when the plugin must reach a network service or specialized local resource.

Remove unused stubs from `plugin.json` (delete the `hooks` and `mcpConfig` keys) to keep the manifest clean.

### 5. Test and iterate

```bash
claude --plugin-dir ./plugins/my-plugin-name
```

- Invoke the skill with `/skill-name` or trigger it by describing a matching task
- For the agent, describe a task matching the agent's description and confirm delegation fires
- Edit SKILL.md files, exit, and reload to iterate

### 6. Install permanently

```bash
claude plugin install ./plugins/my-plugin-name
```

## Plugin manifest fields

```json
{
  "name": "my-plugin",          // kebab-case slug
  "description": "...",         // shown in plugin listings
  "version": "0.1.0",           // semver
  "author": { "name": "..." },
  "license": "MIT",
  "keywords": [],               // used for discovery
  "skills": ["./skills/..."],   // array of skill directories
  "agents": ["./agents/..."],   // array of agent directories
  "hooks": "./hooks/hooks.json",
  "mcpConfig": "./.mcp.json"
}
```

## Hook events

- `PreToolUse` — fires before any tool call; can block or modify
- `PostToolUse` — fires after any tool call; can observe results
- `Notification` — fires on Claude notifications
- `Stop` — fires when Claude finishes a turn

## MCP server config

The `${CLAUDE_PLUGIN_ROOT}` variable expands to the plugin directory at runtime,
so you can bundle server binaries inside the plugin directory.
