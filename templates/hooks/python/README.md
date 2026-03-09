# Python Hook Template

Pre/post edit hooks for Python files. Runs linting and formatting tools automatically
when Claude writes or edits `.py` files in your project.

## Tools supported

All tools are **opt-in** — enable only what your project uses.

| Tool | Role | Enable var | Install |
|---|---|---|---|
| `ruff` | Linting + auto-fix + formatting | `ENABLE_RUFF=1` | `pip install ruff` |
| `black` | Formatting (classic) | `ENABLE_BLACK=1` | `pip install black` |
| `flake8` | Linting (classic, check-only) | `ENABLE_FLAKE8=1` | `pip install flake8` |
| `mypy` | Static type checking | `ENABLE_MYPY=1` | `pip install mypy` |

> **Formatting note:** If both `ENABLE_RUFF=1` and `ENABLE_BLACK=1` are set, ruff formats
> first and black is skipped (avoids double-formatting conflict).

> **Type checking alternative:** `pyright` is a faster alternative to `mypy`.
> To use it, set `ENABLE_MYPY=1` and replace the `mypy` call in `post-edit.sh` with
> `pyright "$FILE_PATH"`.

## Install

```bash
# 1. Copy scripts into your project
mkdir -p .claude/hooks/python
cp /path/to/my-skills/templates/hooks/python/scripts/* .claude/hooks/python/
chmod +x .claude/hooks/python/*.sh

# 2. Merge into .claude/settings.json — replace HOOK_DIR with the absolute path:
#    e.g. /home/user/myproject/.claude/hooks/python
```

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "/abs/path/to/.claude/hooks/python/pre-edit.sh" }]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "/abs/path/to/.claude/hooks/python/post-edit.sh", "timeout": 30 }]
      }
    ]
  }
}
```

## Enabling tools

Set environment variables before starting Claude (in your shell profile, `.envrc`, or
project activation script):

```bash
export ENABLE_RUFF=1      # fast linting + formatting (recommended default)
export ENABLE_MYPY=1      # type checking (slower, add when types matter)
# export ENABLE_BLACK=1   # if project uses black instead of ruff format
# export ENABLE_FLAKE8=1  # if project uses flake8
```

## Behavior reference

| Hook | What runs | On issues |
|---|---|---|
| `pre-edit.sh` | Check-only (no modifications) | Exit 1 — Claude sees warnings, edit proceeds |
| `post-edit.sh` | Auto-fix tools run in-place; check-only tools report | Exit 1 on check failures; exit 0 after auto-fix |

Files that are not `.py` are silently ignored. New files (not yet on disk) are also
skipped by `pre-edit.sh`.
