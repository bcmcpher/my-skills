# Claude Code Configuration: Portability and Reuse

## Config scope: global vs project

| Scope | Location | Who it affects |
|-------|----------|----------------|
| Global | `~/.claude/` | All projects on this machine |
| Project | `.claude/` in the repo root | This project only (checked in or gitignored) |

Global config travels machine-to-machine via dotfiles. Project config travels with the
repo — or can be copied from another project with a similar stack.

---

## Global config — what's portable (`~/.claude/`)

These files can be copied machine-to-machine via a dotfiles repo:

| File | Why |
|------|-----|
| `~/.claude/settings.json` | Global permissions, hooks, enabled plugins |
| `~/.claude/hooks/*.sh` | Hand-authored hook scripts |
| `~/.claude/skills/*/` | Manually installed custom skills |
| `CLAUDE.md` files | Per-project memory (track within each repo) |

---

## Project config — what's copyable (`.claude/` in another repo)

When starting a new project, check whether an existing project with a similar stack
already has these configured — copying is faster than generating from scratch.

| File | How to reuse |
|------|--------------|
| `hooks.json` | Copy to new project; adjust tool matchers and file-path patterns; verify tool names are still valid for this project's stack |
| `.mcp.json` | Copy the entire file or individual server blocks; check that required env vars (`$GITHUB_TOKEN`, etc.) are still set on this machine |
| `agents/<name>/SKILL.md` | Agent prompts are mostly project-agnostic; copy and customize the `description` and any project-specific constraints in the body |
| `skills/<name>/SKILL.md` | Project slash commands; copy if the workflow transfers (e.g., a `/run-tests` skill works across projects of the same language) |
| `.lsp.json` | Copy if the target project uses the same language; the config is usually identical across projects of the same stack |

---

## What to never copy

| File/Dir | Why |
|----------|-----|
| `~/.claude.json` | Auth tokens, session state — machine-specific, sensitive |
| `~/.claude/.credentials.json` | API keys — never track |
| `~/.claude/projects/` | Session history, per-project state |
| `~/.claude/plugins/` | Plugin registry cache — auto-regenerated |
| `~/.claude/cache/`, `statsig/`, `telemetry/` | Runtime caches |
| `~/.claude/todos/`, `plans/`, `tasks/` | Ephemeral session state |

---

## Settings schema notes

- Evaluation order: `deny → ask → allow` (first match wins, deny always wins)
- `defaultMode` options: `default`, `acceptEdits`, `plan`, `bypassPermissions`
- Tool specifier formats: `Bash(cmd *)`, `Read(path)`, `Edit(path)`, `Write`, `WebFetch(domain:x.com)`

---

## Hook registration format

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "~/.claude/hooks/script.sh" }]
    }
  ]
}
```

Hook exit codes: `0` = allow, `2` = block operation. Input arrives via stdin as JSON;
extract `tool_input.file_path` with `jq`.

This format applies to both `~/.claude/settings.json` (global hooks) and
`.claude/hooks.json` (project-level hooks) — same schema, different scope.

---

## Portability mechanics

- Back up `~/.claude/settings.json`, `~/.claude/hooks/`, `~/.claude/skills/` to a dotfiles repo
- On a new system: clone dotfiles, symlink individual files (not the directory — unreliable)
- XDG (`~/.config/claude/`) is NOT supported; `CLAUDE_CONFIG_DIR` is partial/undocumented
