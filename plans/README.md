# plans/

Design documents for work that is scoped but not yet built. A plan lands here when it is
substantial enough to outlive a session and specific enough to execute from — not as a
placeholder for an idea.

Each plan states its own status in its opening lines. That line is the source of truth; this
table is the index.

| Plan | Date | Status | What would unblock it |
|---|---|---|---|
| [zotero-citation-export-pipeline](./zotero-citation-export-pipeline.md) | 2026-09-03, extended 2026-09-04 | Draft — not approved, not started | Answering the 9 ranked questions in "Still to check". The two that gate the design: whether `zotero-cli read` shares the silent truncation found in `get fulltext` (if so, the plan's extraction benchmark was measured through a capped surface), and whether BBT citekeys are pinned (unpinned keys mean a re-run builds a second export tree instead of updating the first). |
| [code-graph-alternatives-eval](./code-graph-alternatives-eval.md) | 2026-09-14 | Screening done — deep review warranted, not started | Approving API spend for the headless exploration runs, plus a held-out item set and a second corpus: the screening tuned CodeGraph's `affected` depth on the same five commits it was scored on. |

## Conventions

- One file per plan, kebab-case, no `PLAN-` prefix — the directory already says that.
- Keep the honest status line at the top, including the parts that did not work. A plan that
  has been partly invalidated by a trial run is more useful with the corrections attached than
  rewritten to look clean.
- When a plan is executed, delete it and let the commit history carry the record.
- Plans that concern a different repository belong in that repository, not here.
