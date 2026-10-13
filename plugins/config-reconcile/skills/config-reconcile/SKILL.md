---
name: config-reconcile
description: Reconcile one project's Claude instructions (CLAUDE.md, CLAUDE.local.md, AGENTS.md, .claude/rules/, and its auto-memory) against the global ~/.claude/CLAUDE.md and its @imports. Classifies each project rule as duplicate, narrower, override, conflict or project-only; reports first, edits only after approval, and records every dropped rule verbatim in a reviewable drop log. Use when the user asks to reconcile, dedupe or align a project's CLAUDE.md or memory with their global defaults.
argument-hint: [project-path]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
---

# Skill: config-reconcile

Reconcile one project at a time. The project is `$ARGUMENTS`, or the current directory if empty.
`<date>` is today as `YYYY-MM-DD`. `<out>` is `${RECONCILE_DIR:-~/.claude/reconcile}/<date>/`.

## Steps

1. **Collect.** Run `bash ${CLAUDE_PLUGIN_ROOT}/skills/config-reconcile/scripts/collect.sh <project>`.
   Read every file it lists: the reference set, the project instruction files, and every memory
   file. Note the `ownership` line. For `fork`, `local` or `not-git`, ask the user whether the
   repo's instruction files are theirs to edit. `upstream` is memory-only: do not propose edits to
   its instruction files.
2. **Classify.** Split each source into rules (a memory file is one rule; a CLAUDE.md bullet or
   paragraph is one rule). Compare each against the reference set and assign one class:

   | Class | Meaning | Action |
   |---|---|---|
   | Duplicate | A global rule already says this | Delete. Memory: delete the file and its `MEMORY.md` line |
   | Narrower | Global covers the general case; the project adds a specific | Rewrite to the delta only |
   | Override | Project deliberately does it differently | Keep; add "Overrides global <file> § <section> because …" |
   | Conflict | Contradicts a global rule with no stated reason | Ask the user: override or delete |
   | Project-only | Global says nothing about it | Keep |

   Judge by meaning, not wording. Facts about the project (commands, layout, data paths) are
   project-only even when they mention git or tools. When unsure between Duplicate and Narrower,
   choose Narrower and quote the part you would keep. Also list housekeeping you saw: dangling or
   unindexed memory links, and memories that look stale. Report these items; do not fix them silently.
3. **Report.** Print one table: `#`, rule (short), class, proposed action, source `file:line` (or
   memory filename), covering global rule (`file § section`). Put Conflicts first with the two
   texts quoted side by side. Then stop and wait. Do not edit anything before the user approves;
   the user may reclassify rows.
4. **Back up memory.** Before any memory edit, copy the whole memory dir to
   `~/.claude/backups/config-reconcile-<date>/<slug>/`. Memory is not in git; the backup is
   the only undo.
5. **Apply.** For instruction files in an owned repo: if the tree is dirty, stop and ask. Otherwise
   create branch `config-reconcile` from the default branch, make the edits, and commit once in the
   repo's `git log` style. Edit memory files in place and keep `MEMORY.md` in step.
6. **Write the drop log.** Owned repo: `<repo>/.claude/reconcile-<date>.md`, committed in the same
   commit. Upstream or memory-only: `<out>/<slug>-dropped.md`. Format:

   ```markdown
   # config-reconcile drop log — <project> — <date>
   Reference set: <global files>. Memory backup: <backup path>.

   ## <n>. <short rule name> — <Duplicate|Narrower>
   Source: <file:line | memory/<file>.md>
   Covered by: <global file> § <section> — "<quoted global text>"
   Removed (verbatim):
   ~~~
   <exact removed text, as whole original lines even when only part of a line changed;
    for a memory, the whole file including frontmatter>
   ~~~
   Kept (Narrower only): <the delta>
   ```

   After the entries, add `## Overrides` and `## Conflicts resolved`, one line each.
7. **Check the log.** Run `bash ${CLAUDE_PLUGIN_ROOT}/skills/config-reconcile/scripts/check-droplog.sh
   <log> [--repo <repo> <default-branch>] [--memory <backup>/ <live-memory-dir>]`. Fix the log
   until it prints `drop log complete`.
8. **Write the summary** to `<out>/<slug>.json`:
   `{"project": path, "ownership": str, "counts": {"duplicate": n, "narrower": n, "override": n,
   "conflict": n, "project_only": n}, "overrides": [{"rule", "global", "reason"}],
   "narrower": [{"rule", "global", "kept"}], "conflicts": [{"rule", "global", "resolution"}]}`.
   Validate with `python3 -I -m json.tool`.
9. **Hand over.** Tell the user the branch, the drop log path, the backup path and
   `git diff <default-branch>...config-reconcile`. Stop. Merge (`--no-ff`) only when the user says so.

## Constraints

- Report before edit, always. One project per run.
- Never edit instruction files in an upstream repo, or anything under `~/.*` outside `~/.claude/`.
- Never push, and never merge without the user's word.
- Never delete a memory without the backup in place and an entry in the drop log.
- Do not reword project-only rules. This pass removes overlap; it does not restyle.
- The reference set is the authority. If a project rule looks better than the global one, still
  classify it, and note it as a candidate for the global pass.
