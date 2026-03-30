# Hooks Configuration Reference

Claude Code hooks run shell commands automatically in response to events. The most
useful pattern for development projects is **PostToolUse Edit** — run a formatter or
linter immediately after Claude edits a file.

**Important:** Claude Code hooks and git pre-commit hooks are independent systems.
Configuring one does not configure the other. See `references/git.md` for git
pre-commit hook tooling (`pre-commit`).

---

## Hook file location

Hooks live in `hooks.json` inside a plugin or in `.claude/hooks.json` for a
project-local configuration.

**Project-local path:** `.claude/hooks.json`

---

## hooks.json format

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "tool": "Edit",
      "command": "<shell command>",
      "description": "<human-readable label>"
    }
  ]
}
```

The `$FILE` variable is expanded to the path of the file that was just edited.

Multiple hooks for the same event are run in order. If any hook exits non-zero, Claude
is notified but execution continues (hooks are advisory, not blocking by default).

---

## Per-language patterns

### Python

**Recommended: ruff (combines linting and formatting)**

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "tool": "Edit",
      "command": "ruff check --fix $FILE && ruff format $FILE",
      "description": "Lint and format Python file with ruff"
    }
  ]
}
```

Install: `pip install ruff` (or `uv add ruff --dev`)

**Alternative: black + flake8**

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "tool": "Edit",
      "command": "black $FILE && flake8 $FILE",
      "description": "Format with black, lint with flake8"
    }
  ]
}
```

**Scope to Python files only** (avoids running on YAML, Markdown, etc.):

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "case $FILE in *.py) ruff check --fix $FILE && ruff format $FILE;; esac",
  "description": "Lint and format Python files only"
}
```

---

### JavaScript / TypeScript

**Recommended: eslint + prettier**

```json
{
  "hooks": [
    {
      "event": "PostToolUse",
      "tool": "Edit",
      "command": "eslint --fix $FILE && prettier --write $FILE",
      "description": "Lint with ESLint, format with Prettier"
    }
  ]
}
```

Install: `npm install --save-dev eslint prettier`

**Biome (unified linter + formatter, faster alternative):**

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "biome check --apply $FILE",
  "description": "Lint and format with Biome"
}
```

---

### Rust

**rustfmt runs on the whole crate — not per-file. Scope to .rs files:**

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "case $FILE in *.rs) cargo fmt -- $FILE;; esac",
  "description": "Format Rust source files"
}
```

**With clippy (slower; runs whole workspace):**

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "case $FILE in *.rs) cargo fmt -- $FILE && cargo clippy --quiet 2>&1 | head -20;; esac",
  "description": "Format and lint Rust"
}
```

---

### Go

**gofmt + goimports:**

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "case $FILE in *.go) goimports -w $FILE;; esac",
  "description": "Format Go file with goimports"
}
```

Install: `go install golang.org/x/tools/cmd/goimports@latest`

Note: `goimports` is a superset of `gofmt` — it formats and manages import grouping.

---

### R

**styler:**

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "case $FILE in *.R|*.Rmd|*.qmd) Rscript -e \"styler::style_file('$FILE')\";; esac",
  "description": "Format R file with styler"
}
```

Install (from R): `install.packages("styler")`

---

### Markdown (any project type)

**prettier:**

```json
{
  "event": "PostToolUse",
  "tool": "Edit",
  "command": "case $FILE in *.md) prettier --write $FILE;; esac",
  "description": "Format Markdown with prettier"
}
```

Note: prettier preserves two trailing spaces (intentional line breaks in Markdown).
Avoid `trim_trailing_whitespace = true` in `.editorconfig` for `.md` files.

---

## Tool config file stubs

When setting up hooks, also offer to create the tool's config file so the hook works
correctly from the first edit rather than relying on defaults.

### Python — `ruff.toml`

```toml
line-length = 88
indent-width = 4
target-version = "py312"

[lint]
select = ["E", "F", "I", "UP"]
ignore = []

[format]
quote-style = "double"
indent-style = "space"
```

### JavaScript / TypeScript — `eslint.config.js` (flat config, ESLint 9+)

```js
import js from "@eslint/js";

export default [
  js.configs.recommended,
  {
    rules: {
      // add project-specific rules here
    },
  },
];
```

Also create `.prettierrc.json`:

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "es5"
}
```

### JavaScript / TypeScript — `biome.json` (if using Biome instead)

```json
{
  "$schema": "https://biomejs.dev/schemas/1.8.0/schema.json",
  "organizeImports": { "enabled": true },
  "linter": {
    "enabled": true,
    "rules": { "recommended": true }
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "space",
    "indentWidth": 2
  }
}
```

### Rust — no separate config needed

`rustfmt` uses `rustfmt.toml` (optional). Defaults are idiomatic; only add a config if
the project needs non-default settings (e.g., `max_width = 100`).

### Go — no separate config needed

`goimports` uses the standard Go formatting rules with no separate config file.

### R — no separate config needed

`styler` uses `tidyverse_style` by default. Add `.styler.R` only if non-default
options are required.

---

## Project-type recommendations

| Project type | Recommended hooks |
|---|---|
| `coding-tool` | Language formatter + linter on every edit. Critical for consistency. |
| `data-analysis` | Formatter only (not linter) on `src/` files. Skip notebooks. |
| `info-management` | Optional Markdown formatter. Usually not needed. |

---

## Disabling hooks for a session

Run Claude with `--no-hooks` to disable all hooks temporarily (useful when hooks are
interfering with exploratory work).
