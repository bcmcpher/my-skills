# Config reconcile skill, then writing-style agents

Status: scoped 2026-10-08, not started. Resume here. First change: the cross-project audit and
reconcile skill. Second change: the two writing agents.

## Where things stand

- Branch `global-claude-md-defaults` (5 commits ahead of `main`, unmerged, not pushed) adds the
  global defaults: `config/{git,specs,engineering,writing}.md` imported by `config/CLAUDE.md`,
  CodeGraph wiring, and the STE evaluation. Design record:
  [`global-claude-md-defaults.md`](./global-claude-md-defaults.md).
- **Already live in `~/.claude/`** (hand-copied 2026-10-08; `settings.json` patched with only the
  graph allow rules and telemetry env). Backup of the previous files:
  `~/.claude/backups/pre-global-defaults-20261008-175020/`.
- VERIFY automated block: all green. Manual rows still to check in an interactive session:
  `/memory` lists the five imports; a question causes no edits; a multi-minute job starts in a
  named tmux session.
- Close-out still to do: `/code-review` passed with 9 fixes applied (`85f6ee2`). Remaining:
  merge to `main` with `--no-ff`, delete `global-claude-md-defaults.md` from `plans/` per the
  plans convention, push only when asked.

## Change 1 — `config-reconcile` skill, then a global pass

Goal: one repeatable pass per project that removes rules the global files now cover, and makes
intentional differences explicit.

**Inputs per project:** `CLAUDE.md`, `CLAUDE.local.md`, `.claude/rules/*.md`, `AGENTS.md`, and the
auto-memory dir `~/.claude/projects/<project>/memory/` (`MEMORY.md` plus topic files).
**Reference set:** `~/.claude/CLAUDE.md` and its imports.

**Classification for each rule:**

| Class | Action |
|---|---|
| Duplicate | Delete. For a memory, delete the file and its `MEMORY.md` line |
| Narrower | Keep only the project-specific delta (e.g. crane's `feat/<change>` naming) |
| Override | Keep, and state it: "Overrides global X because …" |
| Conflict | Ask the user; resolve as override or delete |
| Project-only | Keep |

**Behaviour:**
1. Report first: a table of rule → class → proposed action → source file:line. No edits.
2. Apply only after approval. CLAUDE.md and `.claude/rules/` edits go on a branch in that repo.
   Memory edits are local files with no commit.
3. Write a machine-readable summary (per project: counts per class, overrides list) to feed the
   global pass.

**Open decisions:**
- Home: a plugin in `plugins/config-reconcile/` or a global skill in `config/skills/`. Both
  `claude-md-management:claude-md-improver` and `revise-claude-md` exist. Check what they already
  do before writing anything.
- Where the per-project summaries collect (proposal: `evaluations/<date>-config-reconcile/`).
- Rule matching: model judgement against the global text, or the `<!-- source: … -->` comments in
  the global files as a hint for which projects to check.

**First targets** (from the 2026-10-08 sweep; verify before acting):

| Project | Likely redundant |
|---|---|
| my-skills | memories `confirm-before-outward-facing-actions`, `never-touch-home-dotfiles`, `sandbox-home-for-foreign-test-suites`, `plans-live-in-the-working-directory`; CLAUDE.md "Git conventions" `git mv` paragraph |
| crane | `feedback_openspec_change_branch`, `_archive_command`, `_pause_between_specs`, `_change_scope_discipline`, `_no_compat_shims`, `_synthetic_fixture_not_gate`; OpenSpec part of `.claude/rules/conventions.md` |
| cv-cca | `feedback_tooling` (uv); `feedback_plan_location` **conflicts** with the global plans rule |
| nb-llm-classify | `feedback_uv` |
| neuroanalytics-datasets | `ask-before-pushing` |
| opencite | `review-outward-facing-content-before-posting` (keep the inherited-numbers rule) |
| data-science-harness | `act-on-direct-instructions` |
| pylife | uv and "harness tools are not project deps" lines in CLAUDE.md |

Also seen: crane's `MEMORY.md` lists a missing `feedback_keep_comments.md`. The
`caveman-plugin-rtk-eval` memory says caveman is off by default, but it is on.

**Global pass (after several projects):** from the summaries, demote a global rule that most
projects override. Promote a project rule that recurs as "narrower" in several projects. Settle
the plans-location rule there.

## Change 2 — two writing-style agents

Goal: dedicated writing passes, separate from the `writing.md` fallback that stays in the global
config.

1. **Scientific manuscript agent.** It edits or drafts manuscript and grant prose in the user's
   voice. The fwdti rule applies: it never edits the draft directly, and it delivers paste-able
   text or a diff. Open: the style source (journal guides, the user's past papers), and the
   handling of citations (zotero-cli and opencite are available).
2. **ASD-STE100 agent.** It rewrites technical docs to STE. The user will provide the approved
   vocabulary.
   - The vocabulary is ASD-licensed. Keep it out of the public-bound repo. Load it from a local
     path; decide where.
   - Extend `evaluations/2026-10-08-ste-docs/ste_check.py` with a dictionary check when the
     vocabulary is available. The checker then becomes the agent's self-check.
   - Measure with the existing A/B harness: fallback `writing.md` vs the agent.

Open for both: agent vs skill form (agents get isolated context, which suits whole-document
passes); which model; how they relate to caveman (not at all — they write files, not chat).

## Dropped

- Porting auto-memory between machines. The docs say it is machine-local; nothing has changed.
  Durable rules belong in tracked CLAUDE.md files instead.

## Loose ends

- `bin/rebuild-tools --freeze` will re-add `bun@1.4.2` to `node-lock.txt` while bun stays
  installed for bids-validator. Drop the line again when it appears.
- npm warns that `@inquirer/*` wants Node ≥22.13; the machine has 22.11.0. Nothing fails yet.
