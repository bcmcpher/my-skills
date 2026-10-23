# Triage

Route every finding to exactly one destination. Record the destination beside the
finding in the triage record, so the audit report stays the record of what was found and
the triage record says what happens to it.

| finding | destination |
|---|---|
| value-neutral source change | the repo's tidy unit (one change or plan for small cleanups) |
| large structural split | its own decomposition unit, after the tidy unit |
| spec merge, fold or rewording | the spec-consolidation unit; markers move in the same commit |
| test parametrize, split, fixture move | the test-consolidation unit, after spec consolidation |
| value-changing (output, warning or error type changes) | its own unit, only if the user agrees |
| rejected | the roadmap's "considered and not adopted" list, with the reason |

Order matters in an OpenSpec repo: spec consolidation moves markers, so it lands before
test consolidation, and the markers then move once.

## OpenSpec specifics

- A merge that changes a requirement's heading needs `## RENAMED Requirements` beside
  `## MODIFIED Requirements`, or the markers that name the old heading fail.
- Every requirement keeps at least one marker. List the markers that move.
- A unit that changes no requirement still states so in its proposal.

## Before creating a unit

Ask the user. A finding does not widen the change that surfaced it.
