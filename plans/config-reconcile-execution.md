# Config reconcile: close out global defaults, build skill, walk projects

## Context

Global defaults (`config/{git,specs,engineering,writing}.md`, imported by `config/CLAUDE.md`) are
live in `~/.claude/` and match the tracked copies. Many per-project CLAUDE.md rules, `.claude/rules/`
files and auto-memories now duplicate or conflict with them. Goal: one repeatable pass per project
that deletes duplicates, trims narrower rules to their delta, states overrides explicitly, and
resolves conflicts with the user. Resume plan: `plans/config-reconcile-and-writing-agents.md`
(Change 1). Existing `claude-md-improver` / `revise-claude-md` do template-quality audits only — no
global-vs-project comparison, no memory handling — so a new skill is justified.

Decisions taken: close out first; build a skill and dogfood on my-skills; scope = own repos'
CLAUDE.md/rules + all non-/tmp auto-memory (upstream repos: memory only); home =
`plugins/config-reconcile/`.

## Step 0 — close out `global-claude-md-defaults`

1. Manual VERIFY rows (`config/VERIFY.md:45-54`): user runs `/memory` (five imports listed); ask a
   question, confirm no edits; tmux row — check with a short job in a scratch dir.
2. `git checkout main && git merge --no-ff global-claude-md-defaults`.
3. Delete `plans/global-claude-md-defaults.md`, update `plans/README.md` row, commit.
4. `git branch -d global-claude-md-defaults`. No push unless asked.

## Step 1 — build `plugins/config-reconcile` (branch `config-reconcile`)

Scaffold: `bin/new-plugin skill config-reconcile`; delete unused `assets/`, `references/` if empty.

`skills/config-reconcile/SKILL.md` (argument: project path, default cwd):
1. Run `scripts/collect.sh <path>` → lists inputs: `CLAUDE.md`, `CLAUDE.local.md`, nested
   `CLAUDE.md`, `.claude/rules/*.md`, `AGENTS.md`, and memory dir
   `~/.claude/projects/<path with / → ->/memory/` (MEMORY.md + topic files). Also flags whether the
   repo is user-owned (git remote owner / user-supplied) → upstream repos are memory-only.
2. Read reference set: `~/.claude/CLAUDE.md` + its `@` imports.
3. Classify each rule: Duplicate → delete (memory: file + MEMORY.md line) · Narrower → keep delta
   only · Override → keep, add "Overrides global X because …" · Conflict → ask user · Project-only
   → keep. Also flag broken MEMORY.md links and stale memories seen in passing.
4. Report first: table rule → class → action → `file:line`. No edits.
5. After approval: back up memory dir to `~/.claude/backups/config-reconcile-<date>/<slug>/`
   (memory is untracked, deletion irreversible); edit memory directly; CLAUDE.md/rules edits on
   branch `config-reconcile` in that repo, one commit in repo's style. No merge/push without asking.
6. **Drop log, reviewable in the repo.** Write `.claude/reconcile-<date>.md` in the repo,
   committed on the `config-reconcile` branch with the edits. One entry per Duplicate or Narrower
   item: source (`file:line` or memory filename), the **verbatim removed text** (full memory file
   body for memories, since they are not in git), class, and the global rule that covers it
   (`git.md` § …, quoted). Overrides and Conflict resolutions are listed too. User reviews the log
   plus `git diff main...config-reconcile` before merge; anything overlooked is restored from the
   log (CLAUDE.md/rules) or the backup (memory). After merge the log stays in history; delete it
   in a follow-up commit only if the user says so. Upstream (memory-only) repos: the log goes to
   `evaluations/<date>-config-reconcile/<slug>-dropped.md` in my-skills instead, since their
   trees are not ours to commit to.
7. Write summary JSON to `evaluations/<date>-config-reconcile/<slug>.json`:
   `{project, owned, counts:{duplicate,narrower,override,conflict,project_only}, overrides:[…],
   narrower:[…]}` — feeds the global pass.

Constraints in SKILL.md: never edit upstream-owned CLAUDE.md; don't touch `~/.*` outside
`~/.claude/`; report-before-edit is mandatory.

Commit plugin, install via `claude plugin install config-reconcile@local`.

## Step 2 — walk projects, one at a time, pause between each

Order (biggest payoff / known conflicts first; verify plan's sweep before acting):
1. my-skills (dogfood; 4 memories + CLAUDE.md `git mv` paragraph) → refine skill, recommit
2. crane (24 mem + `.claude/rules/conventions.md`; missing `feedback_keep_comments.md` link)
3. data-science-harness (19) · fwdti-plots (13) · cv-cca (**plans-location conflict**)
4. nb-llm-classify · pylife · opencite · neuroanalytics-datasets
5. memex, memex-trial2, memex-vault, wikiskill, prevent-ad-*, emacs-d, datalad-hpc, cns-calgary,
   cli2mcp, `Projects/claude`
6. Upstream, memory only: datalad, k-dense/scientific-agent-skills, life (if upstream)
7. CLAUDE.md-only repos with no memory dir: study-spec, research-skills, skills-comm (check
   ownership; claude-code-best-practice likely upstream → skip)

Per project: run skill → user reviews table and settles conflicts → apply → drop log + summary
JSON → user verifies drop log and diff → merge `--no-ff` only on user's word → stop.

## Step 3 — global pass

From the summaries: demote a global rule most projects override; promote a project rule that
recurs as Narrower in several; settle plans-location rule (cv-cca). Edits to `config/*.md` on
the `config-reconcile` branch in my-skills, then `bin/sync-config push`. Then `/code-review`,
merge `--no-ff`, update `plans/README.md` (delete Change 1 part of resume plan).

## Verification

- `bin/graduate config-reconcile` passes.
- Dogfood: on my-skills, report lists the 4 known duplicate memories + `git mv` paragraph; after
  apply, `MEMORY.md` has no dangling links (`grep -o '([^)]*\.md)'` vs files) and backup exists.
- Drop log completeness: every memory file missing from the live dir vs the backup, and every
  `-` line in the branch diff, has an entry in the drop log (check by script in the skill).
- Each project: `git -C <repo> diff main...config-reconcile` reviewed by user; summary JSON valid
  (`python -I -m json.tool`).
- After global pass: `diff config/CLAUDE.md ~/.claude/CLAUDE.md` etc. clean; `/memory` in a
  fresh session lists imports.
