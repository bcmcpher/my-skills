# Global CLAUDE.md defaults: git order, spec tools, engineering rules, STE-80 docs

Status: live in `~/.claude/` since 2026-10-08; branch reviewed (fixes in `85f6ee2`), not merged.
STE A/B done: keep `writing.md` (79% → 97%). Next work: `config-reconcile-and-writing-agents.md`.

## Context

`config/CLAUDE.md` (synced to `~/.claude/CLAUDE.md`) covers only harness tool environments.
The same behavioural rules get re-taught per project, through ~150 memory files across 30
project dirs and in typed corrections (git: 208 hits / 18 projects; behaviour: 17 projects;
OpenSpec: 7 projects; uv/venv: 6+ projects). Per-project memory is fragile. In one case the
opencite posting rule never loaded because that project had no `MEMORY.md`.

Goal: a tracked default global CLAUDE.md that gives consistent behaviour across projects. Each
rule is a default that a project CLAUDE.md can override. The user reviews the full draft before
it is pushed live.

Decisions already made:
- Layout: CLAUDE.md stays an index of `@import` topic files, like `@RTK.md`.
- Commit style: follow the repo's `git log`. Use plain imperative sentence case when the repo has
  no history.
- Karpathy gist: take only the rules that fill gaps (below). Skip the rules that duplicate the
  system prompt (#3 surgical, #8 read-first, #11 conventions, #12 fail loud). Skip the app-design
  rules (#5 model-for-judgment, #6 token budgets). #1 "ask when unsure" conflicts with the
  user's "act on direct instructions" memory.
- STE (ASD-STE100) applies at about 80% to user-facing docs and READMEs only. It does not apply
  to specs (the spec tool's own rules win), manuscripts, or chat (caveman stays). The user mainly
  wants a way to *test* compliance.
- Plan-file location: draft it as an overridable default so the user can decide in context.

## Files

| File | Change |
|---|---|
| `config/CLAUDE.md` | Add a short preamble ("defaults; a project CLAUDE.md overrides") and `@git.md @specs.md @engineering.md @writing.md`. Keep the harness section. |
| `config/git.md` | new |
| `config/specs.md` | new |
| `config/engineering.md` | new |
| `config/writing.md` | new |
| `bin/sync-config` | Add `copy_file` lines for the 4 new files in both pull (~l.63) and push (~l.95), matching the existing explicit pattern |
| `config/README.md` | Add the new files to the table at l.14. Fix the stale `~/CLAUDE.md` reference at ~l.270 (that file does not exist). |
| `config/RTK.md` | Fix or drop the dead "Refer to CLAUDE.md for full command reference" line (optional, note only) |
| `config/VERIFY.md` | Add a check that the imports load |
| `plans/global-claude-md-defaults.md` | Named copy of this plan, per the my-skills memory |
| `evaluations/2026-10-08-ste-docs/` | STE checker plus a staged A/B evaluation (see below) |

Budget: about 120 new lines across the 4 files. Every line loads in every session in every
project. Each rule needs evidence from the transcripts or memories. Mark each with a
`<!-- source: … -->` comment so later pruning is easy.

## Draft content (rule sources in brackets)

**git.md**
1. Work on a branch named after the change (or the repo's `type/slug` convention). Experimental
   or risky edits stay off main. [crane, datalad-hpc, fwdti, prevent-ad]
2. Commit at each completed task group or logical step. Unrelated fixes go in separate commits.
   [data-science-harness, my-skills]
3. Commit source only, never data, results, `dev-data/`, or talk material. [fwdti, pylife, crane, dsh]
4. Use `git mv` for tracked files. Promote this from my-skills CLAUDE.md. [my-skills, fwdti]
5. Close-out order: `/code-review` → fix → archive spec (tool command) → commit → merge `--no-ff`
   → push → delete branch. Pause between changes, not between task groups. [crane, datalad-hpc, dsh]
5a. Mid-change review: recommend `/code-review` (do not auto-run it) at a commit boundary when
   any of these is true since the branch point or since the last review:
   - The diff is ≥ about 400 changed lines (`git diff --shortstat <base>...HEAD`). Review
     effectiveness drops past 200–400 LOC per review (SmartBear/Cisco study).
   - About half of the spec's tasks are checked (`tasks.md` `- [x]` vs `- [ ]`) and the diff is
     not trivial.
   - The change touched shared code: a public API, a schema, a CLI interface, or a module other
     code imports.
   - The next step builds on the current code (a refactor, or a new layer on top).

   Track the last review point with a local-only ref (`git update-ref refs/review/<branch> HEAD`).
   It is never pushed. The pre-merge review then covers only the remaining diff plus a quick
   full-branch pass. No hook at first. If the rule gets ignored, a later option is a PostToolUse
   hook on `git commit` that prints the nudge.
6. Push, open PRs, or post comments only on an explicit request at that moment. Plan approval
   does not count. Show the full outward-facing text verbatim, especially @-mentions.
   [neuroanalytics, opencite, my-skills, k-dense]
7. On "save/leave/WIP", commit WIP plus a resume note immediately. Do no further work. [dsh, memex-vault, pylife]
8. Commit message style follows `git log`. Use the repo's author/co-author convention.

**specs.md** (tool-agnostic; covers `openspec/` and `.specify/`)
1. Do not add a spec tool to a repo that has none.
2. The tool's own config, rules, and skills win over this file. Examples: `openspec/config.yaml`
   `rules:`, the `/opsx:*` and `/speckit.*` commands.
3. Before implementing a change, present what it will land and its open decisions, and get
   sign-off. Raise decisions; do not invent them. [dsh, crane]
4. Refer to changes by name, not step number. One branch per change. Archive with the CLI
   (`openspec archive <name> --yes`), never `git mv`. [crane, datalad-hpc]
5. A finding discovered mid-change becomes its own change, not scope creep. [crane]
6. When asked to refresh stale specs, make them match what was implemented. [crane]

**engineering.md** (Karpathy gaps plus history)
1. Use the simplest sufficient mechanism. No speculative abstraction. No compat shims before
   release; prefer clean breaks. [Karpathy #2, memex, crane]
2. A question is not a request for changes. A direct "do X" is the go-ahead; do not re-ask.
   [fwdti, dsh]
3. Surface conflicting patterns: pick one, say why, flag the other. [Karpathy #7]
4. Define verifiable success criteria for multi-step work. Build a synthetic fixture instead of
   deferring a feature for lack of real data. [Karpathy #4, crane]
5. Do not over-claim. Re-measure inherited numbers, check outliers before reporting correlations,
   and verify once against a live run, not only fixtures. [Karpathy #9/#12 gap, fwdti, crane, opencite, wikiskill]
6. Long-running processes run in a named tmux session, never as harness background tasks, so
   they outlive the Claude session and the user can attach to them. Pattern:
   `tmux new-session -d -s <project>-<task> '<cmd> 2>&1 | tee logs/<task>.log'`. Then report the
   session name, `tmux attach -t <name>`, and the log path. To check progress, use
   `tmux capture-pane -pt <name>` or the log. Do not poll. HPC batch work still follows the
   project's own rules (SLURM scripts the user submits). Hand-curated drafts get paste-able
   output, not direct edits. [user, 2026-10-08; fwdti, prevent-ad, k-dense]
7. Environments: the default is `uv venv` / `uv pip` / `uv run`, never bare `pip`. If the user or
   project names a conda env, use that env and call its interpreter by explicit path. Call the
   project `.venv/bin/python` explicitly, because bare `python` resolves to the harness venv.
   [cv-cca, nb-llm, pylife, crane, fwdti, datalad, neuroanalytics]
8. Never edit `~/.*` config outside `~/.claude/` unless asked. Run foreign test suites,
   installers, and `init` commands with `HOME="$(mktemp -d)"`. Sibling/reference repos are
   read-only. [my-skills, opencite, pylife, memex]
9. Plans: use a descriptive filename and write a named copy into the project's `plans/` (or root).
   *Overridable default; cv-cca currently says the opposite.* [my-skills vs cv-cca]

**writing.md** (STE-80 as the fallback style)
- Role: the fallback style for technical docs. It applies when a project sets no doc style of its
  own. It is not an enforced standard.
- Scope: READMEs and user-facing docs written to disk. Not chat (caveman/output style governs
  that), not spec artifacts, not manuscripts or grant text.
- Jargon: define a technical term inline at its first use. Also record it in the project
  glossary (`GLOSSARY.md`, `docs/glossary.md`, or a "Key terms" section), which is the
  authority on what each term means. If no glossary exists and project terms accumulate, offer to
  create one. After a term is defined, use exactly that term. Do not use synonyms. This is the STE
  "one word, one meaning" rule applied to project vocabulary.
- Rules: one topic per sentence. Procedural sentences ≤20 words, descriptive ≤25. Active voice.
  Imperative mood for instructions, one instruction per sentence. Steps go in numbered lists.
  One term per concept, used consistently. No hedges. Avoid -ing nouns and phrasal verbs.
  Paragraphs ≤6 sentences.
- Note: this is "STE-inspired". The approved STE dictionary is ASD-licensed, so it is not
  vendored and not enforced.

## STE testing (evaluations/2026-10-08-ste-docs/)

Staged, per the `tool-evals-are-staged` memory: the first pass only decides whether deeper work
is worth it.
1. `ste_check.py`: stdlib only, run with `python3 -I`. It strips code fences, tables, and links,
   splits sentences, and flags: length over limit, passive (be + past-participle heuristic),
   -ing forms, a small non-approved word list (utilize, in order to, leverage, …), and
   multi-instruction sentences. Output: % of sentences with zero flags, plus per-rule counts.
   80% = target score.
2. Calibrate on existing docs: `config/README.md`, 3 plugin READMEs, and one other project
   README. Check that the scores match intuition. Tune the heuristics, not the target.
3. A/B: `claude -p` writes a README for one fixture plugin, n=3 with `writing.md` imported and
   n=3 without. Compare score distributions. Write a `README.md` with the decision, following
   the existing `evaluations/` format.
4. Optional later: port the rules to Vale if the script proves useful. Check first for an
   existing community Vale STE package.

## Permissions for tmux (settings.json, propose and confirm before editing)
- Add the read-only commands to `allow`: `Bash(tmux ls*)`, `Bash(tmux list-sessions*)`,
  `Bash(tmux capture-pane *)`, `Bash(tmux has-session *)`.
- Leave `tmux new-session` and `tmux kill-session` prompting, so the user sees each launch.

## Out of scope / follow-ups (note, don't do)
- Pruning per-project memories that the new globals duplicate. Do this after the user approves
  the globals.
- Stale/broken memories found: crane `MEMORY.md` lists a missing `feedback_keep_comments.md`.
  The `caveman-plugin-rtk-eval` memory says caveman is off by default, but it is active.

## Verification
1. `bin/sync-config push --dry-run`, if the script supports it. Otherwise diff `config/` against
   `~/.claude/` after push. Run push only after the user reviews the drafts.
2. In a new session, `/memory` lists `~/.claude/CLAUDE.md` with all 4 imports. Add this as a
   VERIFY.md line.
3. `wc -l config/*.md`: new files total ≤ about 120 lines.
4. Behaviour probes in a scratch repo (`mktemp -d`, `git init`). Ask
   `claude -p "implement X then commit"`, then check for a branch, no push, and the commit style.
   Ask "why does Y do Z?" and check that no files changed.
5. `bin/test-hooks` and `bin/rebuild-tools --check` stay green. No hook changes expected.
6. tmux probe: ask a scratch session to run `sleep 120 && echo done`. Expect a named tmux session,
   attach instructions, and a log path. The session should survive after `claude -p` exits
   (`tmux ls`).
7. STE: `python3 -I evaluations/2026-10-08-ste-docs/ste_check.py config/README.md` prints a score.
