# references/

Reference documentation the agent reads on demand.

Keeps the system prompt (`SKILL.md` body) concise by moving large specs,
policies, lookup tables, or background context here. The agent reads them
when needed rather than loading them on every invocation.

For large files (300+ lines), add a table of contents at the top.

Reference from the agent's `SKILL.md`:

```markdown
If you need the full policy details, read `references/policy.md`.
```

Delete this directory if the agent needs no external reference material.
