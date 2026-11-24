# references/

Reference documentation the agent reads on demand.

Keeps the system prompt (the body of `agents/AGENT_NAME.md`) concise by moving large specs,
policies, lookup tables, or background context here. The agent reads them
when needed rather than loading them on every invocation.

For large files (300+ lines), add a table of contents at the top.

Reference from the agent file:

```markdown
If you need the full policy details, read `references/policy.md`.
```

Delete this directory if the agent needs no external reference material.
