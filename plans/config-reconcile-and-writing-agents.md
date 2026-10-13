# Config reconcile skill, then writing-style agents

Status: Change 1 done 2026-10-13. Change 2 not started.

Change 1 built `plugins/config-reconcile/`, walked every project with it, and ran a global pass
that folded recurring project overrides into `config/engineering.md` (Plans, Environments) and
`config/git.md` (Outward-facing actions). Per-project drop logs and summaries are in
`~/.claude/reconcile/2026-10-12/` and `2026-10-13/`; memory backups in
`~/.claude/backups/config-reconcile-2026-10-1{2,3}/`.

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

- `config/VERIFY.md`: the "ask a question, confirm no edits" row was still unchecked when this
  plan was last updated.
- pylife: once its `config-reconcile` branch is merged on the other machine, drop CLAUDE.md
  § Planning — the global Plans rule now covers it (deferred from the global pass).
- User-side: merge cli2mcp `config-reconcile` (3 tests fail on Click 8.5, before and after);
  decide on k-dense's remote `datalad-stamped-checklist` branch and fwdti-plots'
  uncommitted `tools/publish_source.sh`.

- `bin/rebuild-tools --freeze` will re-add `bun@1.4.2` to `node-lock.txt` while bun stays
  installed for bids-validator. Drop the line again when it appears.
- npm warns that `@inquirer/*` wants Node ≥22.13; the machine has 22.11.0. Nothing fails yet.
