# Claude Code Settings Reference

## Settings hierarchy (highest → lowest priority)

| Scope | File | Committed? | When to use |
|---|---|---|---|
| **Enterprise managed** | platform policy | N/A | Org-wide lockdowns; overrides everything |
| **CLI flags** | `--permission-mode`, `--allowedTools`, etc. | N/A | Per-invocation overrides; scripted runs |
| **Local project** | `.claude/settings.local.json` | **No** (gitignore it) | Machine-specific overrides; personal tokens |
| **Project** | `.claude/settings.json` | **Yes** | Shared team config; project permissions |
| **Global/user** | `~/.claude/settings.json` | via `bin/sync-config` | Your personal defaults across all projects |

Later entries in the list have lower priority. A permission in `settings.json` wins over one in `~/.claude/settings.json`.

---

## Permissions model

Permissions live under `"permissions"` with three buckets:

```json
"permissions": {
  "allow": ["Bash(git status)", "Read", "Edit(/src/**)"],
  "ask":   ["Bash(npm install *)", "Write"],
  "deny":  ["Bash(rm -rf *)", "Read(~/.ssh/*)"]
}
```

- `allow` — proceed without confirmation
- `ask` — prompt the user before executing (default for most tools)
- `deny` — block outright, even if the user tries to approve

**Glob patterns** apply to the argument: `Bash(git *)` matches any git subcommand.
**Path patterns** apply to the file argument: `Edit(/src/**)` limits edits to the src tree.

### What belongs where

| Thing | Scope |
|---|---|
| Credentials, personal tokens | Local project (`.claude/settings.local.json`) |
| Project-wide tool allowances (e.g., `npm install`) | Project (`.claude/settings.json`) |
| Security denies (rm -rf, ssh keys) | Global (`~/.claude/settings.json`) |
| Format/lint hook commands | Project (`.claude/settings.json`) |
| Model preference | Global |

---

## Environment variables

Set under `"env"` at the top level:

```json
"env": {
  "ANTHROPIC_API_KEY": "...",
  "MY_PROJECT_ENV": "dev"
}
```

Prefer **local project settings** for secrets; prefer **project settings** for non-sensitive env vars shared across the team.

---

## Output style

```json
"outputFormat": "text"     // "text" | "json" | "stream-json"
```

`json` and `stream-json` are useful for scripted/piped Claude invocations. Leave unset for interactive sessions.

---

## Hooks in settings

Hooks registered in settings apply at that scope — project hooks run for all sessions in the project; global hooks run everywhere.

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit",
      "hooks": [{ "type": "command", "command": "npm run lint --fix" }]
    }
  ]
}
```

Scopes stack: both global and project hooks fire; they do not override each other.

---

## Status line

```json
"statusLine": {
  "type": "command",
  "command": "bash ~/.claude/statusline-command.sh"
}
```

See `reference/statusline.md` for the full command contract and available fields.
