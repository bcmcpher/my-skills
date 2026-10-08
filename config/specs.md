# Spec tools (OpenSpec, spec-kit)

Defaults for repos that contain `openspec/` or `.specify/`. Do not add a spec tool to a repo
that has none.

- The tool's own configuration wins over this file: `openspec/config.yaml` `context:` and
  `rules:`, the project's `/opsx:*` or `/speckit.*` commands and skills, and any spec rules in
  the project's CLAUDE.md. The writing style in `writing.md` does not apply to spec artifacts.
- Before implementing a change, present what it will land and its open decisions, and wait for
  sign-off. Raise decisions; do not invent answers to them.
<!-- source: data-science-harness, crane -->
- Refer to a change by its name, not by a step or list number.
- One branch per change, named after the change (see `git.md` for the close-out order).
- Archive with the tool's command — `openspec archive <name> --yes` — never with `git mv`.
  The OpenSpec CLI is `~/.claude-node-tools/bin/openspec`.
<!-- source: crane, datalad-hpc -->
- A problem found during a change becomes a new change. Do not widen the current one.
<!-- source: crane -->
- When asked to refresh stale specs, make them describe what was implemented.
