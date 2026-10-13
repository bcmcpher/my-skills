# config-reconcile drop log — my-skills — 2026-10-12

Reference set: `~/.claude/CLAUDE.md` + `RTK.md`, `git.md`, `specs.md`, `engineering.md`,
`writing.md`. Memory backup: `/home/bcmcpher/.claude/backups/config-reconcile-2026-10-12/-home-bcmcpher-Projects-claude-my-skills`.
Restore a CLAUDE.md item from the text below; restore a memory by copying it back from the backup.

## 1. Never touch ~/.* config — Duplicate
Source: memory/never-touch-home-dotfiles.md
Covered by: engineering.md § Home directory and other repos — "Do not edit `~/.*` configuration outside `~/.claude/` unless the user asks."
Removed (verbatim):
~~~
---
name: never-touch-home-dotfiles
description: Never create or modify config files under ~/.* unless explicitly asked or they belong to Claude Code
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30b08b2-4fe9-4c52-bfeb-097bd59cefd5
  modified: 2026-09-03T19:55:46.591Z
---

Never create, edit, or overwrite a config file under `${HOME}/.*` unless the user explicitly
asked for that specific change, or the file is part of Claude Code itself (`~/.claude/`).
This covers tool configs like `~/.opencite/`, `~/.config/<tool>/`, shell rc files, and anything
else in a home dotfile or dotdir.

**Why:** on 2026-09-03 I ran a third-party project's test suite against the real `$HOME` and it
wiped `~/.opencite/config.toml`, destroying API keys the user had spent an afternoon obtaining
and configuring. Earlier in the same session I had also run `opencite config init` and hand-edited
that file. The user's words: "NEVER modify config files in ${HOME}/.* that aren't explicitly
requested by me or are a part of claude-code."

**How to apply:** treat `~/.*` as read-only by default. To set a value in a tool's config, tell
the user the exact edit and let them make it, or ask first — do not "helpfully" apply it. Running
a foreign test suite, installer, or `<tool> init` counts as modifying these files even when the
write is indirect; see [[sandbox-home-for-foreign-test-suites]]. `~/.claude/` remains fair game
for ordinary harness work, and the repo's own `config/` tree is the source of truth for that —
see [[config-is-one-way-baseline]].
~~~

## 2. Sandbox HOME for foreign test suites — Duplicate
Source: memory/sandbox-home-for-foreign-test-suites.md
Covered by: engineering.md § Home directory and other repos — "Run third-party test suites, installers and `init` commands with a throwaway home: `env HOME="$(mktemp -d)" <cmd>`."
Removed (verbatim):
~~~
---
name: sandbox-home-for-foreign-test-suites
description: Run third-party test suites with HOME redirected to a temp dir; they can write to real user config
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30b08b2-4fe9-4c52-bfeb-097bd59cefd5
  modified: 2026-09-03T19:55:57.759Z
---

Before running another project's test suite, installer, or `init`-style command, redirect `HOME`
to a throwaway directory:

```bash
env HOME="$(mktemp -d)" .venv/bin/python -m pytest tests/
```

**Why:** on 2026-09-03, `pytest tests/` in a clone of `neuromechanist/opencite` overwrote the
real `~/.opencite/config.toml` and destroyed the user's API keys. `tests/test_cli.py` exercises
`config init` while monkeypatching only `XDG_CONFIG_HOME`, but `config.py` computes
`CONFIG_DIR = Path.home() / ".opencite"` as a module-level constant, and `create_default_config()`
does an unconditional `write_text()` with no existence check. Confirmed by reproducing it against
a sentinel file in a sandboxed `HOME`.

**How to apply:** a passing test suite is not evidence that it is side-effect free. Assume any
foreign code run locally may write to `$HOME`. Sandboxing `HOME` costs nothing and is the only
reliable guard, since these writes bypass the `Edit`/`Write` tool hooks entirely — `protect-files.sh`
never sees them. Related: [[never-touch-home-dotfiles]].
~~~

## 3. Plans live in the working directory — Duplicate
Source: memory/plans-live-in-the-working-directory.md
Covered by: engineering.md § Plans — "Give a plan a descriptive kebab-case filename, and write a copy into the project (its `plans/` directory, or the root if there is none)."
Removed (verbatim):
~~~
---
name: plans-live-in-the-working-directory
description: "Save plan documents into the current project directory with a clear filename, not ~/.claude/plans"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d30b08b2-4fe9-4c52-bfeb-097bd59cefd5
  modified: 2026-09-03T21:59:13.876Z
---

When a planning session produces a plan worth keeping, write it into the current working
directory under a clearly descriptive filename (e.g. `PLAN-zotero-citation-export-pipeline.md`),
not only to the harness's `~/.claude/plans/<random-slug>.md`.

**Why:** on 2026-09-03 the user rejected `ExitPlanMode` with: "Save this plan in the current
directory with a clearly named title. I'll move it myself to a dedicated target directory when I
resume refining the plan." The harness plan file is auto-named from the first prompt
(`i-would-like-to-foamy-crown.md`), which says nothing about the contents and is not where the
user goes to find or refine a plan later.

**How to apply:** the harness plan file is scratch for the plan-mode workflow. For any plan the
user intends to revisit, also write a named copy into the repo and let them relocate it — do not
pick a destination directory for them. Related: [[config-is-one-way-baseline]].
~~~

## 4. Confirm before outward-facing actions — Narrower
Source: memory/confirm-before-outward-facing-actions.md
Covered by: git.md § Outward-facing actions — "Push, open a PR, or post an issue or comment only when the user asks for it at that moment. Approval of a plan is not approval to publish. A project may grant a standing authorization in its own CLAUDE.md or memory."
Removed (verbatim):
~~~
---
name: confirm-before-outward-facing-actions
description: Confirm at execution time before any push/PR/comment outside my-skills, or any public text that @-mentions a person
metadata:
  type: feedback
---

Stop and confirm **at the moment of acting**, not just when the plan is approved, before:

1. Any push, PR, issue, or comment on a repo other than `bcmcpher/my-skills` — including
   closing or commenting on someone else's PR.
2. Any text I publish that names or @-mentions another person, even in a repo Brent owns.

**Why:** in the 2026-09-11 session I opened `K-Dense-AI/scientific-agent-skills#265` and closed
`dylanpulver/scientific-agent-skills#2` with a comment. Both steps were listed in an approved
plan and in a selected AskUserQuestion option, so they were authorized — but the approval had
happened many steps earlier, and Brent's reaction was "why didn't you verify with me". Approval
to *prepare* a branch is not the same decision as approval to *publish* it into someone else's
org, where the PR notifies maintainers and the @-mentions name real people. Collapsing the two
is the error, even when the earlier approval technically covers it.

**How to apply:** do all the local work — branch, cherry-pick, run the gates, draft the body —
then surface the finished artifact and ask before the call that publishes it. Show the body text
when it mentions anyone. Pushes to `bcmcpher/my-skills` itself do **not** need this; Brent
explicitly left those alone. Related: [[proj_datalad-kdense-reconciliation]].
~~~
Kept: the standing authorization for pushes to `bcmcpher/my-skills` (memory file rewritten).

## 5. git mv for tracked files — Duplicate
Source: CLAUDE.md:175-184 (pre-reconcile)
Covered by: git.md § Branches and commits — "Move tracked files with `git mv`; check with `git ls-files --error-unmatch <path>`."
Removed (verbatim):
~~~
## Git conventions

Before moving any file, check whether it is tracked:

```bash
git ls-files --error-unmatch <path>
```

- If tracked → use `git mv <src> <dst>`, not bare `mv`. This preserves rename history and keeps `git blame` accurate.
- If not tracked (new or ignored file) → bare `mv` is fine.
~~~

## 6. Hook-history opener — Narrower
Source: CLAUDE.md:186 (pre-reconcile)
Covered by: — (rewording only; the section now opens on the global rule)
Removed (verbatim):
~~~
This is a convention, not an enforced rule. The `git-guard.sh` hook that used to enforce it was
removed: its second rule matched `.git/` anywhere in the command text, which blocked the ordinary
~~~
Kept: section retitled "## Guard hooks"; rest of the paragraph unchanged.

## 7. Harness tools live in the two venvs — Narrower
Source: CLAUDE.md:35-36 (pre-reconcile)
Covered by: CLAUDE.md (global) § Harness tool environments — table of Python/Node homes; "Harness tools are not project dependencies."
Removed (verbatim):
~~~
Harness tools — hook binaries, LSP servers, and the CLIs that global skills shell out to — live in
`~/.claude-lsp-tools` (a `uv venv`) and `~/.claude-node-tools` (an npm prefix), never in a project
environment. `bin/rebuild-tools` recreates both from the manifests in `config/tools/` and verifies
~~~
Kept: the `bin/rebuild-tools` sentence.

## 8. LSP install snippet — Narrower
Source: CLAUDE.md:105-111 (pre-reconcile)
Covered by: CLAUDE.md (global) § Harness tool environments — "`uv pip install --python ~/.claude-lsp-tools/bin/python <pkg>`"
Removed (verbatim):
~~~
Recommended pattern: keep Python LSP binaries in a dedicated venv on `$PATH`, independent of any project venv:

```bash
uv venv ~/.claude-lsp-tools
uv pip install --python ~/.claude-lsp-tools/bin/python pyright
# export PATH="$HOME/.claude-lsp-tools/bin:$PATH"  ← in shell rc
```
~~~
Kept: a one-line pointer to the global section; the three-layer table stays.

## Housekeeping done

- Indexed `tool-evals-are-staged.md` in `MEMORY.md` (was unindexed).
- Refreshed `proj_config-reconcile-and-writing-agents.md` (it still said to do the close-out first).

## Overrides

None.

## Conflicts resolved

None.

## Noted, not changed

- `plan_obsidian-memory-integration.md` is a full plan stored as a memory (status "research" since
  2026-03). Candidate to move to `plans/`.
