# Full Plugin Template — Setup Guide

> This file is a setup reference. Replace it with your plugin's `README.md` when done.

Copy this directory to `plugins/my-plugin-name`, then:

1. Rename `skills/SKILL_NAME/` and `agents/AGENT_NAME/` directories
2. Edit `.claude-plugin/plugin.json` — update all placeholder values
3. Edit the `SKILL.md` files — fill in frontmatter and bodies
4. Replace this file (`SETUP.md`) with your plugin's `README.md`
5. Delete unused resource subdirectories (`scripts/`, `references/`, `assets/`)
6. Add hooks or MCP config only if you need them (see sections below)
7. Test: `claude --plugin-dir ./plugins/my-plugin-name`

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

### 4. Bundle resources (optional)

Each skill/agent directory has three optional subdirectories:

```
skills/your-skill/
├── SKILL.md
├── scripts/      # Deterministic helper scripts (avoids re-implementing logic per invocation)
├── references/   # Large docs loaded on demand (keeps SKILL.md concise)
└── assets/       # Static files for output (templates, fonts, icons)
```

- **`scripts/`** — If every invocation would otherwise re-write the same helper script, bundle it once and reference it from `SKILL.md` via `${CLAUDE_PLUGIN_ROOT}/skills/your-skill/scripts/`.
- **`references/`** — Move large lookup tables, API specs, or style guides here. Add a table of contents for files over 300 lines.
- **`assets/`** — Output templates, logos, fonts, or other static files the skill embeds.

Delete any subdirectory you don't use.

### 5. Add hooks (optional)

Hooks run shell commands in response to Claude events. Only add them when you have a specific need — they fire on every matching event.

To activate hooks:
1. Copy `hooks/hooks.json.example` to `hooks/hooks.json`
2. Edit `hooks/hooks.json` — replace placeholder commands with real ones
3. Add `"hooks": "./hooks/hooks.json"` to `plugin.json`

Available events:
- `PreToolUse` — fires before any tool call; can block or modify
- `PostToolUse` — fires after any tool call; can observe results
- `Notification` — fires on Claude notifications
- `Stop` — fires when Claude finishes a turn

### 6. Add MCP servers (optional)

MCP servers give the plugin access to external services or specialized resources beyond Claude's built-in tools. Only needed when the plugin must reach a network service or specialized local resource.

To activate MCP config:
1. Edit `.mcp.json` — replace the example server entry with your real server config
2. Add `"mcpConfig": "./.mcp.json"` to `plugin.json`

The `${CLAUDE_PLUGIN_ROOT}` variable expands to the plugin directory at runtime, so you can bundle server binaries inside the plugin.

### 7. Test and iterate

```bash
claude --plugin-dir ./plugins/my-plugin-name
```

- Invoke the skill with `/skill-name` or trigger it by describing a matching task
- For the agent, describe a task matching the agent's description and confirm delegation fires
- Edit SKILL.md files, exit, and reload to iterate

### 8. Install permanently

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

  // Add only when needed:
  "hooks": "./hooks/hooks.json",
  "mcpConfig": "./.mcp.json"
}
```
