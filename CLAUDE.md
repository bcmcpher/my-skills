# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common commands

```bash
# Scaffold a new plugin from a template
bin/new-plugin <type> <name>   # type: skill | agent | hook; name: kebab-case

# Test a plugin in a session-only context (no permanent install)
claude --plugin-dir ./plugins/<name>

# Install a plugin permanently (user scope)
claude plugin install ./plugins/<name>

# Sync global ~/.claude/ config
bin/sync-config pull           # ~/.claude/ → config/  (after changing settings in Claude)
bin/sync-config push           # config/ → ~/.claude/  (apply to a new machine)
```

## Architecture

This is a monorepo of Claude Code plugins and global config. Each plugin lives in `plugins/<name>/` and is independently installable. Templates in `templates/` serve as copy-paste starters. `config/` tracks the user-level `~/.claude/` files that are portable across machines.

### Plugin anatomy

```
plugins/<name>/
├── .claude-plugin/plugin.json   # Manifest: name, description, version, skills[], agents[]
├── skills/<skill-name>/
│   ├── SKILL.md                 # Frontmatter + instruction body (the core artifact)
│   ├── scripts/                 # Helper scripts invoked from SKILL.md via $CLAUDE_PLUGIN_ROOT
│   ├── references/              # Large docs loaded on demand (keep SKILL.md concise)
│   └── assets/                  # Static files embedded in output
├── agents/<agent-name>/
│   └── SKILL.md                 # Agent system prompt with frontmatter
├── hooks/hooks.json             # PreToolUse / PostToolUse / Stop hook definitions
└── .mcp.json                    # MCP server config (uses $CLAUDE_PLUGIN_ROOT for paths)
```

### SKILL.md frontmatter — skills vs agents

**Skills** (`skills/<name>/SKILL.md`):
```yaml
name: skill-name          # becomes /skill-name slash command
description: ...          # Claude reads this to decide auto-invocation — be specific
argument-hint: [optional] # shown in autocomplete UI
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob
```

**Agents** (`agents/<name>/SKILL.md`):
```yaml
name: agent-name
description: ...          # delegation trigger for the main Claude instance
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
maxTurns: 20
```

The body of a SKILL.md is imperative prose: numbered steps, then constraints. Reference `$ARGUMENTS` for user input, and `${CLAUDE_PLUGIN_ROOT}` in scripts paths.

### plugin.json fields

`skills` and `agents` are arrays of relative paths to the skill/agent directories. Omit `hooks` and `mcpConfig` keys entirely when not used — don't leave them empty.

### Key design rules

- **`description` quality is critical**: for skills, it controls auto-invocation reliability; for agents, it controls when the main Claude delegates. Vague descriptions cause misfires.
- **`references/`** is for large lookup tables or specs — move content there when SKILL.md exceeds ~100 lines.
- **`scripts/`** is for deterministic logic that would otherwise be re-implemented per invocation.
- Delete unused `scripts/`, `references/`, `assets/` subdirectories — empty dirs add no value.
- Replace `SETUP.md` with `README.md` when a plugin is done.

### Templates

| Template | Use when |
|----------|----------|
| `templates/skill/` | Slash command or auto-invoked instruction only |
| `templates/agent/` | Specialized subagent with isolated context |

`bin/new-plugin` copies the chosen template, renames placeholder dirs, and replaces `PLUGIN_NAME`/`SKILL_NAME`/`AGENT_NAME` tokens automatically. For a full plugin with hooks or MCP, see `reference/plugin/` as a structural reference.

## Git conventions

Before moving any file, check whether it is tracked:

```bash
git ls-files --error-unmatch <path>
```

- If tracked → use `git mv <src> <dst>`, not bare `mv`. This preserves rename history and keeps `git blame` accurate.
- If not tracked (new or ignored file) → bare `mv` is fine.

The `git-guard.sh` PreToolUse hook will block bare `mv` on tracked files and explain the correct command. `git mv` is in the allow list and proceeds without confirmation.
