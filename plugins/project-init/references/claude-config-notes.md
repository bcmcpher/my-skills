# Claude Code Global Configuration Notes

## Files to Back Up (minimal portable set)

| File | Why |
|------|-----|
| `~/.claude/settings.json` | Global permissions, hooks, enabled plugins |
| `~/.claude/hooks/*.sh` | Hand-authored hook scripts |
| `~/.claude/skills/*/` | Manually installed custom skills |
| `CLAUDE.md` files | Per-project memory (track within each repo) |

## Files to NOT Back Up

| File/Dir | Why |
|----------|-----|
| `~/.claude.json` | Auth tokens, session state — machine-specific, sensitive |
| `~/.claude/.credentials.json` | API keys — never track |
| `~/.claude/projects/` | Session history, per-project state |
| `~/.claude/plugins/` | Plugin registry cache — auto-regenerated |
| `~/.claude/cache/`, `statsig/`, `telemetry/` | Runtime caches |
| `~/.claude/todos/`, `plans/`, `tasks/` | Ephemeral session state |

## Settings Schema Notes

- Evaluation order: `deny → ask → allow` (first match wins, deny always wins)
- `defaultMode` options: `default`, `acceptEdits`, `plan`, `bypassPermissions`
- Tool specifier formats: `Bash(cmd *)`, `Read(path)`, `Edit(path)`, `Write`, `WebFetch(domain:x.com)`

## Hook Registration Format

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

Hook exit codes: `0` = allow, `2` = block operation. Input arrives via stdin as JSON; extract `tool_input.file_path` with `jq`.

## Portability Strategy

- Back up `~/.claude/settings.json`, `~/.claude/hooks/`, `~/.claude/skills/` to a dotfiles repo
- On a new system: clone dotfiles, symlink individual files (not the directory — unreliable)
- XDG (`~/.config/claude/`) is NOT supported; `CLAUDE_CONFIG_DIR` is partial/undocumented
