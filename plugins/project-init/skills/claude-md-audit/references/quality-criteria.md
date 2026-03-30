# CLAUDE.md Quality Criteria

Reference for Phase 2 of the claude-md-audit skill. Load this file when scoring a
CLAUDE.md to apply the detailed rubric.

---

## Scoring Rubric (100 points total)

### Commands / workflows (20 pts)

| Points | Condition |
|---|---|
| 18–20 | Build, test, run, and lint commands all present; copy-paste ready |
| 12–17 | Most commands present; one or two missing |
| 6–11 | Only one category of commands documented |
| 0–5 | No commands, or commands that no longer work |

Look for: `## Common commands`, `## Quick Start`, or equivalent sections. Check
whether the commands actually match what's in `package.json`, `Makefile`,
`pyproject.toml`, etc.

### Architecture clarity (20 pts)

| Points | Condition |
|---|---|
| 18–20 | Directory structure explained; key files named; entry points identified |
| 12–17 | Structure partially documented; some key files missing |
| 6–11 | Vague description ("this is a Python project") with no structure |
| 0–5 | No architecture documentation |

Look for: directory trees, file purpose tables, entry point identification.

### Non-obvious patterns (15 pts)

| Points | Condition |
|---|---|
| 13–15 | Gotchas, quirks, and project-specific rules clearly documented |
| 8–12 | Some non-obvious patterns noted; others missing |
| 3–7 | Only obvious or generic patterns mentioned |
| 0–2 | Nothing project-specific |

Examples of non-obvious patterns worth capturing:
- "Never edit X without running Y first"
- "Module Z must be imported before module W due to side effects"
- "The test suite requires a running Docker daemon"
- "All data files are symlinked from /data — do not copy them"

### Conciseness (15 pts)

| Points | Condition |
|---|---|
| 13–15 | Tight, human-readable; no filler; dense is better than verbose |
| 8–12 | Mostly concise; a few wordy sections |
| 3–7 | Notable filler or redundant explanations |
| 0–2 | Verbose throughout; takes >5 min to read |

Deductions for:
- Restating what's obvious from the code or file structure
- Generic best practices already covered by any style guide
- Section headers with no meaningful content under them

### Currency (15 pts)

| Points | Condition |
|---|---|
| 13–15 | Reflects the current codebase; no stale references |
| 8–12 | Mostly current; one or two outdated items |
| 3–7 | Several stale entries (old dependencies, renamed paths, changed commands) |
| 0–2 | Clearly outdated; multiple broken or misleading entries |

Check for stale content by:
- Comparing listed commands against actual `package.json` / `Makefile` scripts
- Verifying file paths in architecture sections still exist
- Checking that named dependencies match `requirements.txt` / `pyproject.toml`

### Actionability (15 pts)

| Points | Condition |
|---|---|
| 13–15 | Every instruction is specific and executable; no vague guidance |
| 8–12 | Mostly actionable; one or two vague instructions |
| 3–7 | Mix of actionable and vague guidance |
| 0–2 | Mostly vague ("be careful with X", "make sure to test") |

Deductions for instructions that:
- Use hedging language without specifics ("you may need to...")
- Reference concepts without naming the file, command, or tool
- Give no context for *when* a rule applies

---

## Common Issues Checklist

When reviewing a CLAUDE.md, actively check for:

- **Stale commands**: Build/test scripts that have changed
- **Missing env vars**: Required environment variables not mentioned
- **Outdated architecture**: Directory structure that has changed
- **Broken test commands**: Test scripts that no longer exist or have moved
- **Missing dependencies**: External tools required but not mentioned
  (e.g., Docker, `gh`, `direnv`, specific CLI tools)
- **Undocumented gotchas**: Non-obvious patterns not captured
- **Length creep**: File approaching 200 lines without `.claude/rules/` split

---

## What a Great CLAUDE.md Looks Like

**Characteristics:**
- A new contributor could onboard from it without asking questions
- All documented commands are copy-paste ready and current
- Project-specific quirks are captured; generic advice is absent
- Sections are focused — each heading has substantive content under it
- Reads in under 2 minutes

**Recommended sections** (include only what's relevant):
- Commands (build, test, dev, lint, deploy)
- Architecture (directory structure, key files)
- Environment (required vars, setup steps, active environment)
- Code style (project-specific conventions, not generic)
- Testing (commands, framework, patterns)
- Gotchas (warnings, quirks, non-obvious rules)
- Workflow (when to do what — PR process, branch conventions, etc.)
