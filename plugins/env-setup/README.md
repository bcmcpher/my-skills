# env-setup

Set up and manage local programming language environments for Claude Code projects.

## Skills

### `/venv`

Detects the project language and sets up the appropriate environment:

| Language | Toolchain |
|---|---|
| Python | `uv venv` (preferred) or `python -m venv` |
| JavaScript | npm / yarn / pnpm, with nvm support |
| TypeScript | npm / yarn / pnpm, with `tsc --noEmit` verify |
| Rust | rustup + cargo fetch/build |
| Go | go mod download / tidy |
| R | renv init / restore |

After setup, documents the environment in `CLAUDE.md` and offers to configure LSP,
hooks, or local skills/agents for the project.

## Usage

```bash
/venv               # auto-detect language from project files
/venv python        # use Python explicitly
/venv --recreate    # delete and recreate existing environment (prompts for confirmation)
```

## Install

```bash
# Session-only test
claude --plugin-dir ./plugins/env-setup

# Permanent install
claude plugin install ./plugins/env-setup
```
