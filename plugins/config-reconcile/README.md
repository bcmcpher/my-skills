# config-reconcile

Align one project's Claude instructions with the global defaults in `~/.claude/CLAUDE.md` and its
`@` imports. The skill reads the project's `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`,
`.claude/rules/*.md` and auto-memory. It sorts each rule into one of five classes and removes
the overlap.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/config-reconcile

# Permanent install — via this repo's marketplace (run from the repo root)
claude plugin marketplace add .
claude plugin install config-reconcile@local        # then restart Claude Code
```

## Use

```
/config-reconcile [project-path]
```

1. The skill lists every input and prints a report table. It makes no edits at this stage.
2. Review the table. Reclassify any row and settle each conflict.
3. On approval, the skill backs up the memory dir and makes the edits on branch
   `config-reconcile`. It writes a drop log and a summary.
4. Review the drop log and `git diff <default>...config-reconcile`. Merge when satisfied.

## Classes

| Class | Action |
|---|---|
| Duplicate | Delete |
| Narrower | Keep only the project-specific part |
| Override | Keep, with a stated reason |
| Conflict | The user decides: override or delete |
| Project-only | Keep unchanged |

## Outputs

| Output | Where |
|---|---|
| Drop log: each removed rule, verbatim, with the global rule that covers it | `<repo>/.claude/reconcile-<date>.md`, committed on the branch. Upstream repos: `<out>/<slug>-dropped.md` |
| Memory backup — the only undo for memory, which is not in git | `~/.claude/backups/config-reconcile-<date>/<slug>/` |
| Summary JSON — class counts, overrides, narrower rules, for a later global pass | `<out>/<slug>.json` |

`<out>` is `$RECONCILE_DIR/<date>/`, default `~/.claude/reconcile/<date>/`.

## Scripts

- `scripts/collect.sh [path]` lists the inputs. It reports repo ownership (owned, fork, upstream,
  local), files identical to a global file, and dangling or unindexed memory links.
- `scripts/check-droplog.sh <log> [--repo <repo> <base>] [--memory <backup> <live>]` confirms
  that the drop log quotes every removed diff line and every deleted memory file. It exits 1 if
  anything is missing.

## Ownership

The skill edits instruction files only in repos the user owns. For an upstream repo it edits
auto-memory only. Forks and repos with no remote are confirmed with the user first.
