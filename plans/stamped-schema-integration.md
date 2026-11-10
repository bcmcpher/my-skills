# Schema-backed STAMPED assessment

Status: draft, moved here from memory 2026-11-09 (first recorded 2026-07). Not started. Not
blocked. One question is still open (see "Open question"); it decides the final checklist, but
Win 2 can start without it.

## Context

The `datalad-stamped-assess` skill in `plugins/datalad-cli/` shipped in PR #4 (merged 2026-07,
closes issue #1). It scores a dataset against a hand-distilled checklist in
`plugins/datalad-cli/references/stamped-principles.md`, walking S.1–D.3.

That list has drifted from the canonical principles. It invents S.2, M.3 and D.3 (license items)
and merges T.4 with T.5. The canonical set is the LinkML data in
`github.com/stamped-principles/stamped-principles-schema` (`stamped-principles.json`). Version
0.1.0 has 16 principles: S.1; T.1–T.5; A.1–A.2; M.1–M.2; P.1–P.3; E.1; D.1–D.2.

On 2026-07-10, yarikoptic endorsed Win 2: a machine-readable record "could be the
source/model for rendering human-readable view". He also suggested that STAMPED itself define a
`STAMPED.yaml` that records the evidence behind a judgement (attention: codycbakerphd, asmacdo).

## Changes

### Win 1: drive the checklist from the canonical data

- Vendor a pinned snapshot of `stamped-principles.json` into the plugin, so the plugin stays
  self-contained. Record the source version and commit next to it.
- Generate or replace the checklist in `references/stamped-principles.md` from the snapshot.
  Remove the invented codes and split T.4 and T.5.

### Win 2: emit a structured assessment

- Define an `Assessment` result model in LinkML that imports the upstream schema. The upstream
  schema models the principles (`Principle{code, category, level, statement}` and
  `PrincipleSet`). It is a question bank, not a report format, so the result model is ours.
- Each evaluation is keyed by the canonical `code` and holds a grade, the evidence and the
  remediation.
- The JSON assessment is the durable artifact. Render the human-readable table from it.
- Optional: record the assessment with `datalad run`, so the audit is itself Tracked.

## Open question

Are the paper's license requirements (S.2, M.3, D.3) left out of schema 0.1.0 on purpose, or
not yet encoded? The answer decides whether the final checklist keeps them. No answer yet.

## Related

- The STAMPED property-to-command mapping went upstream as
  `K-Dense-AI/scientific-agent-skills#265` (open, awaiting review on 2026-09-11). Keep the local
  skill and the upstream one from diverging.
- Verify command claims against a matching DataLad build first.
