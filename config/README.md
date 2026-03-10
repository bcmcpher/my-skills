# config/ — Global Claude Code configuration

Versioned copy of the portable files from `~/.claude/`. Use `bin/sync-config` to keep this
directory and your live config in sync.

## What's tracked

| File | Source | Purpose |
|---|---|---|
| `settings.json` | `~/.claude/settings.json` | Enabled plugins, permissions, global hooks wiring |
| `hooks/protect-files.sh` | `~/.claude/hooks/protect-files.sh` | PreToolUse guard — blocks edits to protected files |
| `skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Standalone globally-installed skills |

## What's NOT tracked

- `~/.claude/.credentials.json` — auth tokens, never commit
- `~/.claude/history.jsonl`, `cache/`, `session-env/`, `projects/` — ephemeral runtime state
- `~/.claude/plugins/` — installed plugin copies; their sources live in `plugins/` in this repo

## Sync workflow

```bash
# Pull live config into this repo (after changing settings in Claude)
bin/sync-config pull

# Push repo config to ~/.claude/ (on a new machine or after editing here)
bin/sync-config push
```

## Adding a new global hook

1. Write the script and place it in `config/hooks/`
2. Wire it in `config/settings.json` under `hooks.PreToolUse` or `hooks.PostToolUse`
3. Run `bin/sync-config push` to apply

## Adding a new standalone skill

Standalone skills (no plugin wrapper) live in `~/.claude/skills/<name>/SKILL.md`.
To track one here:

1. Copy `~/.claude/skills/<name>/` into `config/skills/<name>/`
2. Run `bin/sync-config pull` going forward to keep it in sync

To promote a standalone skill to a full plugin, copy it to `plugins/<name>/` using
`bin/new-plugin skill <name>` and move the SKILL.md content there.
