# project-init

Scaffold and configure new projects for use with Claude Code. Covers project structure,
programming environment, and Claude-specific tooling across three project types:
**coding tool / package**, **data analysis**, and **information management**.

## Skills

### `/new-project` — primary wizard

Guides through a complete project setup in one workflow:

1. Choose project type (coding-tool, data-analysis, info-management)
2. Scaffold directory structure and essential files
3. Initialize git and hygiene checks
4. Set up the programming environment (skipped for info-management)
5. Write a project-type CLAUDE.md template
6. Configure Claude Code tooling (LSP, hooks, MCP, agents)

```bash
/new-project                        # interactive — asks type and name
/new-project coding-tool my-lib     # explicit type and name
/new-project data-analysis          # explicit type, asks for name
/new-project info-management vault  # info vault (no env setup)
```

---

### `/env-check` — environment validation

Validates, creates, updates, or recreates the programming environment for an existing
project. Documents the environment in `CLAUDE.md`.

| Language | Toolchain |
|---|---|
| Python | `uv venv` (preferred) or `python -m venv` |
| JavaScript | npm / yarn / pnpm, with nvm support |
| TypeScript | npm / yarn / pnpm, with `tsc --noEmit` verify |
| Rust | rustup + cargo |
| Go | go mod download / tidy |
| R | renv init / restore |

Conda environments are documented in CLAUDE.md with activation instructions rather
than created inline (conda requires pre-session activation).

```bash
/env-check              # auto-detect language from project files
/env-check python       # use Python explicitly
/env-check --recreate   # delete and recreate (prompts for confirmation)
```

---

### `/claude-config` — Claude Code configuration

Configures Claude Code tooling for any project. Safe to run at any time; safe to
re-run to add options later.

Options:

| # | Option | Notes |
|---|---|---|
| 1 | CLAUDE.md | Generate or update with project-type content |
| 2 | LSP | Language server for diagnostics and navigation |
| 3 | Hooks | PostToolUse formatter / linter automation |
| 4 | MCP servers | DataLad, web search, GitHub integrations |
| 5 | Agents | Project-specific subagents in `.claude/agents/` |
| 6 | Local skills | Project-specific slash commands in `.claude/skills/` |
| 7 | `.editorconfig` | Consistent editor settings |

```bash
/claude-config                  # detect project type from CLAUDE.md or ask
/claude-config data-analysis    # explicit project type
```

---

## Install

```bash
# Session-only test
claude --plugin-dir ./plugins/project-init

# Permanent install
claude plugin install ./plugins/project-init
```

## Reference files

```
references/
├── git.md                        # gitignore entries, secrets pattern, hook distinction
├── editorconfig.md               # per-language editor settings
├── python.md / javascript.md / typescript.md / rust.md / go.md / r.md
├── project-types/
│   ├── coding-tool.md            # scaffold spec, CI stubs, CLAUDE.md template, agents
│   ├── data-analysis.md          # cookiecutter structure, DataLad guidance, agents
│   └── info-management.md        # vault structure, CLAUDE.md template, agents
└── claude-config/
    ├── lsp.md                    # LSP setup by language
    ├── hooks.md                  # PostToolUse hook patterns by language
    └── mcp.md                    # MCP server recommendations by project type
```
