# references/

Reference documentation loaded into context when Claude needs it.

Keep the main `SKILL.md` concise by moving large lookup tables, API docs,
style guides, or format specs here. Claude reads them on demand rather than
having them in context permanently.

For large files (300+ lines), add a table of contents at the top so Claude
can navigate without reading the whole file.

Reference from `SKILL.md` with a note on when to read:

```markdown
Read `references/api-spec.md` for the full list of supported parameters.
```

Delete this directory if the skill has no reference material.
