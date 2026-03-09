# Hook Templates

Reusable per-project hook scripts for Claude Code. These are **copy-to-project** templates —
not plugins. Drop them into any project's `.claude/` directory and merge the config into
`.claude/settings.json`.

## How hooks work

Claude Code hooks fire shell commands at specific events:

| Event | When | Common use |
|---|---|---|
| `PreToolUse` | Before a tool call | Lint check, safety guard |
| `PostToolUse` | After a tool call | Auto-fix, formatting |
| `Stop` | When Claude finishes a turn | Notifications, summaries |

Exit codes control behavior:

| Code | Meaning |
|---|---|
| `0` | Success — proceed normally |
| `1` | Warning — show output to Claude, but continue |
| `2` | Block — abort the operation, show output as error |

## Available templates

| Language | Tools supported |
|---|---|
| [`python/`](python/) | ruff, black, mypy, flake8 |

## Install workflow

```bash
# 1. Copy scripts into your project
mkdir -p .claude/hooks/python
cp /path/to/my-skills/templates/hooks/python/scripts/* .claude/hooks/python/
chmod +x .claude/hooks/python/*.sh

# 2. Merge hooks.json into your project's .claude/settings.json
#    Open templates/hooks/python/hooks.json, copy the "PreToolUse" and "PostToolUse"
#    blocks, and paste them under the "hooks" key in .claude/settings.json.
#    Replace HOOK_DIR with the absolute path to .claude/hooks/python in your project.

# 3. Enable tools via environment variables (in your shell profile or project .envrc):
#    export ENABLE_RUFF=1
#    export ENABLE_MYPY=1
```

## Adding hooks to `.claude/settings.json`

If `settings.json` does not exist yet:

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

If `hooks` already exists, merge the arrays — do not replace the entire key.
