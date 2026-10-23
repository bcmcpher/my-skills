# Report template

Write the report to the path the project uses for audits (for example
`examples/<name>-audit.md`). Sections, in order:

## 1. Header

- commit audited (`git rev-parse HEAD`), date, tool and model;
- commands run, and the script reports saved;
- package versions that affect results (`python`, type checker, stubs, main libraries).

## 2. Summary

Ten lines or fewer: the three most important themes.

## 3. Test baseline

Pass/skip counts, wall clock, coverage totals, modules below the project's coverage floor.

## 4. Findings

| id | status | area | location | category | value-neutral? | confidence | finding | proposed fix |
|---|---|---|---|---|---|---|---|---|

- `id`: A1… B1… C1…, continuing across passes; never reuse a withdrawn id.
- `status`: `new`, `kept`, `revised` (say what changed) or `withdrawn` (say why).
- `location`: `file:line`. For a pattern: one row, every site, and the count.
- `value-neutral?`: `Yes` with the proving test, or `No` with what changes.

## 5. Proposed work units

Group findings into units sized for one reviewable change. Give order and dependencies.

## 6. Checked and sound

One line per dimension with no finding:

> **<dimension>:** <method>, <count> examined; <what was found and why it is sound>.

A line without a method and a count is not accepted.
