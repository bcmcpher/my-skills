# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common commands

```bash
# Scaffold a new plugin from a template
bin/new-plugin <type> <name>   # type: skill | agent | hook | mcp; name: kebab-case

# Test a plugin in a session-only context (no permanent install)
claude --plugin-dir ./plugins/<name>

# Install a plugin permanently (user scope)
claude plugin install ./plugins/<name>

# Check a plugin is fully converted from its template and ready to publish
bin/graduate <plugin-name>

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
├── .mcp.json                    # MCP server config (uses $CLAUDE_PLUGIN_ROOT for paths)
└── .lsp.json                    # LSP server config (optional; binary installed separately)
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

### LSP servers

Claude Code uses standard LSP servers for real-time code intelligence: diagnostics after each file edit, and precise code navigation (go-to-definition, find-references) beyond grep. Configure via `.lsp.json` at the plugin root; add `"lspConfig": "./.lsp.json"` to `plugin.json`.

**The binary must be installed separately** — `.lsp.json` only tells Claude Code how to connect. LSP tools are not codebase dependencies.

Recommended pattern: keep Python LSP binaries in a dedicated venv on `$PATH`, independent of any project venv:

```bash
python -m venv ~/.claude-lsp-tools
~/.claude-lsp-tools/bin/pip install pyright
# export PATH="$HOME/.claude-lsp-tools/bin:$PATH"  ← in shell rc
```

Per-project type awareness (e.g., which `.venv` pyright checks) is controlled by language-specific project config files (`pyrightconfig.json`, `tsconfig.json`), not `.lsp.json`. The three layers are independent:

| Layer | Where |
|-------|-------|
| LSP binary | `~/.claude-lsp-tools/` or system `$PATH` |
| Claude connection config | `.lsp.json` in the plugin |
| Project environment | `pyrightconfig.json`, `tsconfig.json`, etc. in the repo |

See `reference/plugin/.lsp.json` for an annotated example covering Python, TypeScript, Go, and Rust.

### plugin.json fields

`skills` and `agents` are arrays of relative paths to the skill/agent directories. Omit `hooks` and `mcpConfig` keys entirely when not used — don't leave them empty.

### Key design rules

- **`description` quality is critical**: for skills, it controls auto-invocation reliability; for agents, it controls when the main Claude delegates. Vague descriptions cause misfires.
- **`references/`** is for large lookup tables or specs — move content there when SKILL.md exceeds ~100 lines.
- **`scripts/`** is for deterministic logic that would otherwise be re-implemented per invocation.
- Delete unused `scripts/`, `references/`, `assets/` subdirectories — empty dirs add no value.
- Replace `SETUP.md` with `README.md` when a plugin is done.

### Shared references across skills

When a plugin contains multiple skills that draw on the same domain knowledge, place `references/` at the plugin level rather than inside each skill:

```
plugins/<name>/
├── references/           # shared across all skills in this plugin
│   ├── topic-a.md
│   └── topic-b.md
├── skills/skill-one/
│   └── SKILL.md          # load with ${CLAUDE_PLUGIN_ROOT}/../references/topic-a.md
└── skills/skill-two/
    └── SKILL.md          # same reference, no duplication
```

Skill-specific references still belong inside the skill directory. Only promote to plugin-level when two or more skills genuinely share the material. Never duplicate a reference file just to keep it co-located.

### Templates

| Template | Use when |
|----------|----------|
| `templates/skill/` | Slash command or auto-invoked instruction only |
| `templates/agent/` | Specialized subagent with isolated context |
| `templates/mcp/` | Add MCP server stubs to an existing plugin |

`bin/new-plugin` copies the chosen template, renames placeholder dirs, and replaces `PLUGIN_NAME`/`SKILL_NAME`/`AGENT_NAME` tokens automatically. For a full plugin with hooks or MCP, see `reference/plugin/` as a structural reference.

`bin/new-plugin mcp <name>` scaffolds three parallel server stubs — Python (FastMCP/uv), TypeScript (MCP SDK/tsx), and Docker — each wired into `.mcp.json`. Delete the ones you won't use and remove their entries from `.mcp.json` before testing.

## Git conventions

Before moving any file, check whether it is tracked:

```bash
git ls-files --error-unmatch <path>
```

- If tracked → use `git mv <src> <dst>`, not bare `mv`. This preserves rename history and keeps `git blame` accurate.
- If not tracked (new or ignored file) → bare `mv` is fine.

The `git-guard.sh` PreToolUse hook will block bare `mv` on tracked files and explain the correct command. `git mv` is in the allow list and proceeds without confirmation.
