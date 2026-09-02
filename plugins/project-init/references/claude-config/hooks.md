# Hooks Configuration Reference

Claude Code hooks run shell commands automatically in response to events. The most
useful pattern for development projects is **PostToolUse on Edit/Write** — run a
formatter or linter immediately after Claude edits a file.

**Important:** Claude Code hooks and git pre-commit hooks are independent systems.
Configuring one does not configure the other. See `references/git.md` for git
pre-commit hook tooling (`pre-commit`).

---

## Where hooks are registered

There are two places, with different shapes. There is no `.claude/hooks.json`.

| Scope | File | Shape |
|---|---|---|
| Project | `.claude/settings.json` | events nested under a top-level `"hooks"` key |
| User (global) | `~/.claude/settings.json` | same |
| Plugin | `<plugin>/hooks/hooks.json`, referenced from `plugin.json` | events at the **top level**, no `"hooks"` wrapper |

Scopes stack — a project hook and a global hook both fire; neither overrides the other.

**Project (`.claude/settings.json`):**

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": ".claude/hooks/format-on-edit.sh", "timeout": 30 }
        ]
      }
    ]
  }
}
```

**Plugin (`hooks/hooks.json`)** — same structure minus the wrapper, and use
`${CLAUDE_PLUGIN_ROOT}` for script paths:

```json
{
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/format.sh" }
      ]
    }
  ]
}
```

`matcher` is a regex over the tool name (`Edit|Write|NotebookEdit`, `Bash`, `.*`).
Omit it for events that have no tool, such as `SessionStart`, `SessionEnd`, and `Stop`.

---

## How a hook receives the file path

**There is no `$FILE` variable.** A hook is a plain command that receives a JSON
event object on **stdin** and reads what it needs from it:

| Field | Meaning |
|---|---|
| `.tool_name` | the tool that fired the event |
| `.tool_input.file_path` | Edit / Write / NotebookEdit target |
| `.tool_input.command` | Bash command text |
| `.cwd` | session working directory |
| `.hook_event_name` | e.g. `PostToolUse` |

Because the payload is JSON, a hook is almost always a **small script**, not an
inline one-liner. Put it in `.claude/hooks/` and commit it.

---

## Exit codes

| Exit | PreToolUse | PostToolUse |
|---|---|---|
| `0` | allow the call | success; stdout ignored |
| `2` | **block** the call; stderr is shown to Claude | stderr is fed back to Claude |
| other | non-blocking error; the call proceeds | non-blocking error |

Hooks are not advisory by default — a `PreToolUse` hook exiting 2 genuinely stops the
tool call. Conversely, a hook that exits non-zero by accident (a status command that
returns 1 when it has nothing to report) will surface as a hook error on every event.
End such scripts with an explicit `exit 0` rather than masking the problem with
`|| true`, which also swallows real failures.

`SessionStart` is the exception worth knowing: its **stdout is added to the session
context**, which is how a hook can report state at session open.

---

## Canonical format-on-edit script

One script per project, dispatching on file extension. Create
`.claude/hooks/format-on-edit.sh`, `chmod +x` it, and wire it as shown above.

```bash
#!/bin/bash
# PostToolUse Edit|Write — format the file Claude just touched.

FILE=$(jq -r '.tool_input.file_path // empty')
[ -n "$FILE" ] && [ -f "$FILE" ] || exit 0

case "$FILE" in
  # <-- per-language arm goes here (see table below)
  *.py) ruff check --fix "$FILE" && ruff format "$FILE" ;;
esac

exit 0
```

`jq` is required. The trailing `exit 0` matters: without it the script's status is
that of the last `case` arm, so a linter finding an issue would report a hook failure.

---

## Per-language `case` arms

Drop the matching arm into the script above.

### Python

**Recommended — ruff (linter and formatter in one):**
```bash
  *.py) ruff check --fix "$FILE" && ruff format "$FILE" ;;
```
Install: `uv add --dev ruff` (or `pip install ruff`)

**Alternative — black + flake8:**
```bash
  *.py) black "$FILE" && flake8 "$FILE" ;;
```

### JavaScript / TypeScript

**Recommended — eslint + prettier:**
```bash
  *.js|*.jsx|*.ts|*.tsx) eslint --fix "$FILE" && prettier --write "$FILE" ;;
```
Install: `npm install --save-dev eslint prettier`

**Biome (unified, faster):**
```bash
  *.js|*.jsx|*.ts|*.tsx) biome check --write "$FILE" ;;
```
`biome check --apply` was renamed to `--write` in Biome 2.x.

### Rust

`rustfmt` formats a whole crate, so the file path is only used to decide *whether* to run:
```bash
  *.rs) cargo fmt ;;
```

**With clippy (slower; checks the whole workspace):**
```bash
  *.rs) cargo fmt && cargo clippy --quiet 2>&1 | head -20 ;;
```

### Go

```bash
  *.go) goimports -w "$FILE" ;;
```
Install: `go install golang.org/x/tools/cmd/goimports@latest`

`goimports` is a superset of `gofmt` — it formats and manages import grouping.

### R

```bash
  *.R|*.Rmd|*.qmd) Rscript -e "styler::style_file('$FILE')" ;;
```
Install (from R): `install.packages("styler")`

### Markdown (any project type)

```bash
  *.md) prettier --write "$FILE" ;;
```

prettier preserves two trailing spaces (intentional line breaks in Markdown).
Avoid `trim_trailing_whitespace = true` for `.md` files in `.editorconfig`.

---

## Tools must resolve without a login shell

Hooks run in a **non-interactive** shell. Anything sourced from `.bashrc` — `nvm`,
`conda activate`, a `pyenv` shim, a `PATH` export — is absent. A hook command that
works when you paste it into your terminal can still fail every time Claude fires it.

Check before wiring:

```bash
env -i PATH="/usr/bin:/bin" bash -c '<cmd> --version'
```

If it fails, use an explicit path in the hook command (`node_modules/.bin/eslint`,
`.venv/bin/ruff`, `~/.claude-lsp-tools/bin/<cmd>`) rather than a bare name. `nvm` is
the classic offender: it is a shell function, so `~/.nvm/versions/node/*/bin` does not
exist on `PATH` where hooks run.

---

## Guard hooks (PreToolUse)

Beyond formatting, `PreToolUse` can block a call outright. Two patterns worth knowing:

**Protect files from edits** — matcher `Edit|Write|NotebookEdit`:
```bash
#!/bin/bash
FILE=$(jq -r '.tool_input.file_path // empty')
for pattern in ".env" "package-lock.json"; do
  if [[ "$FILE" == *"$pattern"* ]]; then
    echo "Blocked: $FILE matches protected pattern '$pattern'" >&2
    exit 2
  fi
done
exit 0
```

**Guard shell commands** — matcher `Bash`, reading `.tool_input.command`.

When writing a Bash guard, match on an **argument position**, not on raw command text.
A rule that greps the whole command string for a substring will fire on that substring
inside a quoted argument or a `--exclude` flag, blocking legitimate commands. Guards
that produce false positives get disabled, which is worse than not having them.

Guards deserve a test table — a file of `command<TAB>expected-exit` cases run through
the script — because a regression in a guard is silent until it blocks real work.

---

## Project-type recommendations

| Project type | Recommended hooks |
|---|---|
| `coding-tool` | Language formatter + linter on every edit. Critical for consistency. |
| `data-analysis` | Formatter only (not linter) on `src/` files. Skip notebooks. |
| `info-management` | Optional Markdown formatter. Usually not needed. |

---

## Disabling hooks for a session

Start Claude with `--bare`, which skips hooks, LSP, and plugins for that session.
There is no `--no-hooks` flag. To disable a single hook, comment it out of
`.claude/settings.json`; to see what fired, start with `--include-hook-events`.
