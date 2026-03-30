# Git reference

## `.gitignore` entries by language

| Language | Add to `.gitignore` |
|---|---|
| Python | `.venv/` |
| JavaScript | `node_modules/` |
| TypeScript | `node_modules/` |
| Rust | `target/` (cargo new adds this automatically; check before adding) |
| Go | *(nothing — `go.sum` should be committed; no env dir to exclude)* |
| R | `renv/library/` (note: `renv.lock` and `renv/activate.R` should be committed) |

## Claude Code local files (all projects)

Always add these entries regardless of language — they contain machine-specific
settings and tokens that must not be committed:

```
# Claude Code local overrides (machine-specific, never commit)
.claude.local.md
.claude/settings.local.json
```

## `git init` guidance

```bash
git init
```

Then create `.gitignore` with the appropriate entry for your language (see table above),
add your project files (not the env directory), and make the first commit:

```bash
git add .gitignore <other project files>
git commit -m "Initial commit"
```

## Claude Code hooks vs git pre-commit hooks

These are independent systems:

- **Claude Code PostToolUse hooks** run while Claude edits files in a session. Configured
  in `hooks.json` inside the plugin or `.claude/` directory.
- **git pre-commit hooks** run before each `git commit`, entirely outside Claude Code.
  Configured and managed by your git tooling.

Configuring one does not configure the other.

For git pre-commit hook management: https://pre-commit.com

---

## `.env` / secrets pattern

| File | Committed? | Purpose |
|---|---|---|
| `.env` | **No** — add to `.gitignore` | Local secrets and overrides |
| `.env.example` | **Yes** | Template with placeholder values, documents required vars |
| `.env.local`, `.env.*.local` | **No** | Convention for local overrides (Next.js, Vite, etc.) |

Rules:

- If `.env` exists and is not in `.gitignore`, it may already contain secrets — offer
  to add it immediately.
- If neither `.env` nor `.env.example` exists, the project likely has no env var
  convention yet. Offer to create `.env.example` as an empty template and add `.env`
  to `.gitignore`.
- If `.env.example` exists but `.env` is not ignored, the pattern is partially set up —
  just fix `.gitignore`.
