---
name: new-project
description: >
  Scaffold a new project for use with Claude Code. Guides through project type selection
  (coding-tool, data-analysis, or info-management), creates the directory structure and
  essential files, initializes git, sets up the programming environment, and configures
  Claude Code tooling — all in a single guided workflow. Use when the user says "start
  a new project", "create a new project", "scaffold a project", "initialize a project",
  or "/new-project". Takes an optional project type and name as arguments.
argument-hint: [coding-tool|data-analysis|info-management] [project-name]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

# Skill: new-project

Scaffold a complete new project for use with Claude Code. Covers structure, environment,
and Claude tooling in one guided workflow.

---

## Phase 0: Project identity

### Step 1 — Parse arguments

Scan `$ARGUMENTS` for a recognized type keyword:

| Keywords | Type |
|---|---|
| "coding-tool", "package", "library", "cli", "tool", "service" | `coding-tool` |
| "data-analysis", "data", "analysis", "research", "science", "notebook" | `data-analysis` |
| "info-management", "info", "notes", "knowledge", "vault", "research-aggregation" | `info-management` |

If a second token exists and matches neither keyword list, treat it as the project name.

### Step 2 — Ask for what is still unknown

**If project type is unknown**, present:

> "What kind of project are you starting?
>
> 1. **Coding tool / package** — a library, CLI, or service; built for programmatic
>    use and potentially external contributors
> 2. **Data analysis** — reproducible research producing models, figures, and reports
>    for distribution
> 3. **Information management** — structured knowledge collection: research aggregation,
>    note-taking, or executive-assistant-style work
>
> Reply with a number or a type name."

Wait for the user's choice.

**If project name is unknown**, ask:

> "What is the project name? (kebab-case, used for the directory and package name)"

Optionally ask for a one-line description (used in README and package manifest stubs).

### Step 3 — Load project type reference

| Type | Reference |
|---|---|
| `coding-tool` | `${CLAUDE_PLUGIN_ROOT}/../references/project-types/coding-tool.md` |
| `data-analysis` | `${CLAUDE_PLUGIN_ROOT}/../references/project-types/data-analysis.md` |
| `info-management` | `${CLAUDE_PLUGIN_ROOT}/../references/project-types/info-management.md` |

**Load this reference before proceeding.** All scaffold content, CLAUDE.md templates,
and configuration recommendations come from it.

---

## Phase 1: Directory check

Check whether `<project-name>/` exists in the current working directory.

- **Does not exist** → proceed.
- **Exists and is empty** → proceed (files will be created inside it).
- **Exists and is non-empty** → warn:

  > "`<project-name>/` already exists and is not empty. Continuing will add scaffold
  > files but will not overwrite anything that already exists.
  >
  > Proceed, or cancel?"

  Wait for confirmation. If cancelled, stop.

---

## Phase 2: Scaffold structure

Create the directory tree and stub files defined in the reference's **Directory
scaffold** and **Essential files** sections.

Rules:

- Create directories with `mkdir -p`.
- For each stub file: check whether it already exists before writing. If it exists,
  skip it and note that it was preserved.
- Substitute `<project-name>` and `<description>` throughout stub content.
- Do not create any file not listed in the reference's scaffold spec.

After scaffolding, briefly list the directories and files created.

---

## Phase 3: Git and secrets hygiene

Load `${CLAUDE_PLUGIN_ROOT}/../references/git.md`.

Run `git rev-parse --is-inside-work-tree` from within `<project-name>/`.

**Not already a git repository** (expected for new projects):

- Run `git init` inside the project directory.
- Write `.gitignore` using the language entries from `references/git.md` plus any
  project-type-specific entries from the loaded reference's **.gitignore additions**
  section.
- Inform the user: "Git initialized. Review the scaffolded files, then run
  `git add . && git commit -m 'Initial commit'` to record the starting state."

**Already inside a git repository** (nested — less common for new projects):

- Run the `.gitignore` coverage check from `references/git.md` for the env directory.
- Offer to add missing entries.

**Secrets check (both cases):**

Follow the `.env` check from `references/git.md`. For new projects neither `.env` nor
`.env.example` will exist — offer to create the pattern unless the project type
reference explicitly advises against it (info-management projects often don't need it).

---

## Phase 4: Environment setup

*Skip this phase for `info-management` projects — they have no programming environment.
Proceed directly to Phase 5.*

### Step 1 — Detect language

Check the reference's **Primary language** field first. If it specifies one, use it.
Otherwise use signal files created during scaffolding (the manifest file created in
Phase 2 is sufficient — no need to re-scan):

| Manifest created | Language | Reference |
|---|---|---|
| `pyproject.toml` | Python | `${CLAUDE_PLUGIN_ROOT}/../references/python.md` |
| `package.json` (no `tsconfig.json`) | JavaScript | `${CLAUDE_PLUGIN_ROOT}/../references/javascript.md` |
| `package.json` + `tsconfig.json` | TypeScript | `${CLAUDE_PLUGIN_ROOT}/../references/typescript.md` |
| `Cargo.toml` | Rust | `${CLAUDE_PLUGIN_ROOT}/../references/rust.md` |
| `go.mod` | Go | `${CLAUDE_PLUGIN_ROOT}/../references/go.md` |
| `renv.lock` / `DESCRIPTION` | R | `${CLAUDE_PLUGIN_ROOT}/../references/r.md` |

**Load the language reference before continuing.**

If no manifest was created (user is working in a language with no scaffold match), ask.

### Step 2 — Conda check (Python only)

Before creating a Python environment, check:
1. `which conda` exits 0
2. `environment.yml` exists in the project root
3. `$ARGUMENTS` contains "conda" or "anaconda"

If **any** signal is true:

> "A conda installation was detected. Conda environments must be activated before
> Claude Code launches — `conda activate` modifies shell state that subprocesses
> cannot inherit.
>
> Options:
> 1. **Use conda manually** — I'll document the setup in CLAUDE.md. You activate
>    before launching Claude Code.
> 2. **Use venv instead** — I'll set up a standard `.venv` (or `uv` env) right now."

- Conda: write environment details to `## Active Environment` in CLAUDE.md (name,
  activate command, Python version from `environment.yml` if present). Note the manual
  activation requirement. Skip Steps 3–4.
- Venv: continue to Step 3.

If no conda signals, skip this step.

### Step 3 — Create environment

This is a new project — no existing environment check needed. Proceed directly to
environment creation using the steps in the loaded language reference.

**Permission-blocked commands:** surface the exact command and wait for "done" before
continuing — do not retry or silently skip.

### Step 4 — Verify

Run the verification command from the language reference. Confirm the interpreter or
toolchain resolves inside the new environment, not a system installation.

If it points to a system binary, report the discrepancy and ask the user how to proceed
— do not declare success.

---

## Phase 5: Document in CLAUDE.md

The project type reference includes a **CLAUDE.md template** section. Write this
template to `<project-name>/CLAUDE.md`.

Rules:

- If CLAUDE.md was already created by Phase 2 scaffolding (some project types include
  it), append or merge — do not overwrite.
- Substitute `<project-name>`, `<description>`, `<language>`, and environment details
  from Phase 4 throughout the template.
- After writing the template, also write or update the `## Active Environment` section
  (format defined in `${CLAUDE_PLUGIN_ROOT}/../skills/env-check/SKILL.md` Phase 4).
  For info-management projects, use:

  ```markdown
  ## Active Environment

  - Language: none (knowledge management project)
  - Last setup: <YYYY-MM-DD>
  ```

---

## Phase 6: Claude Code configuration

Load `${CLAUDE_PLUGIN_ROOT}/../skills/claude-config/SKILL.md` and execute its full
workflow. The project type and language are already established — pass them as context
so the skill skips its detection steps and goes directly to the configuration menu.

The user will receive the full menu of configuration options (CLAUDE.md refinement, LSP,
hooks, MCP servers, agents, local skills, `.editorconfig`) without needing to invoke
`/claude-config` separately.

---

## Constraints

- Never overwrite a file that already exists during scaffolding — skip and note it.
- Never skip the conda check when any conda signal is present (Python only).
- Do not create files outside `<project-name>/` unless the user explicitly requests it.
- If a Bash command is blocked, surface the exact command and wait for "done" — do not
  retry or silently skip.
- The CLAUDE.md template from the project type reference is the authoritative content
  for Phase 5 — do not invent project-specific instructions beyond what the template
  specifies.
- Always verify the environment before declaring Phase 4 complete.
