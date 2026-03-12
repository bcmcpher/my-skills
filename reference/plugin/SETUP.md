# Full Plugin Template — Setup Guide

> This file is a setup reference. Replace it with your plugin's `README.md` when done.

## Contents inventory

Every file and directory in this reference — what it is, whether it's required, and when to remove it.

| Path | Status | Keep when |
|------|--------|-----------|
| `.claude-plugin/plugin.json` | Always | — |
| `README.md` | Always (replace SETUP.md) | — |
| `SETUP.md` | Delete when done | Replace with `README.md` |
| `skills/<name>/SKILL.md` | Conditional | plugin exposes a slash command or auto-invoked skill |
| `skills/<name>/scripts/` | Optional | skill has deterministic helper logic to bundle |
| `skills/<name>/references/` | Optional | skill has large docs to load on demand |
| `skills/<name>/assets/` | Optional | skill embeds static files in output |
| `agents/<name>/SKILL.md` | Conditional | plugin includes a delegatable subagent |
| `agents/<name>/scripts/` | Optional | same as skill scripts |
| `agents/<name>/references/` | Optional | same as skill references |
| `agents/<name>/assets/` | Optional | same as skill assets |
| `hooks/hooks.json` | Conditional | plugin needs PreToolUse / PostToolUse / Notification / Stop hooks |
| `.mcp.json` | Conditional | plugin exposes MCP servers |
| `servers/` | Conditional | `.mcp.json` uses a local `stdio` server bundled in the plugin |
| `.lsp.json` | Conditional | plugin needs LSP code intelligence (diagnostics, go-to-definition) |

---

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

### 7. Add LSP servers (optional)

LSP servers give Claude real-time code intelligence: diagnostics (type errors, missing imports) after each edit, and precise code navigation (go-to-definition, find-references) instead of grep-based search.

**Important:** `.lsp.json` tells Claude Code *how to connect* to a language server. The binary must be installed separately — it is not a codebase dependency.

To activate LSP:
1. Copy `.lsp.json` from this reference — delete entries for languages you don't use
2. Add `"lspConfig": "./.lsp.json"` to `plugin.json`
3. Install the required binary (see table below)

| Language | Binary | Install |
|----------|--------|---------|
| Python | `pyright` | `pip install pyright` or `npm install -g pyright` |
| TypeScript | `typescript-language-server` | `npm install -g typescript-language-server typescript` |
| Go | `gopls` | `go install golang.org/x/tools/gopls@latest` |
| Rust | `rust-analyzer` | See rust-analyzer install docs |

**Recommended binary management:** keep Python LSP tools in a dedicated venv that is always on `$PATH`, separate from project venvs:

```bash
python -m venv ~/.claude-lsp-tools
~/.claude-lsp-tools/bin/pip install pyright
# Add to ~/.bashrc: export PATH="$HOME/.claude-lsp-tools/bin:$PATH"
```

**Per-project type awareness** (e.g., which `.venv` pyright should analyze) is configured in language-specific project files — not in `.lsp.json`:

| Language | Config file | Key fields |
|----------|-------------|------------|
| Python | `pyrightconfig.json` | `venvPath`, `venv` |
| TypeScript | `tsconfig.json` | `compilerOptions` |
| Go | `go.mod` | automatic |

This keeps concerns separate: the LSP binary location, the Claude connection config, and the project environment are all independent layers.

### 8. Test and iterate

```bash
claude --plugin-dir ./plugins/my-plugin-name
```

- Invoke the skill with `/skill-name` or trigger it by describing a matching task
- For the agent, describe a task matching the agent's description and confirm delegation fires
- Edit SKILL.md files, exit, and reload to iterate

### 9. Install permanently

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
  "mcpConfig": "./.mcp.json",
  "lspConfig": "./.lsp.json"
}
```
