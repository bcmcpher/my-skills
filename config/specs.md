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
- One branch per change (see `git.md` for its name and the close-out order).
- In a superproject with submodules, branch every repo the change touches under the same name.
  Code commits go to the submodule branch; spec deltas, docs and `tasks.md` ticks go to the
  parent branch, which pins the submodule at its branch HEAD. Merge the submodule first, then
  the parent, so the parent never pins a commit that is not on the submodule's default branch.
  Merge the submodule with `--no-ff`, not a squash or rebase, so the pinned commit stays
  reachable. Archive on the parent branch.
- Archive with the tool's command — `openspec archive <name> --yes` — never with `git mv`.
  The OpenSpec CLI is `~/.claude-node-tools/bin/openspec`.
<!-- source: crane, datalad-hpc -->
- Implement a change one numbered task section at a time (`## 1.`, `## 2.` … in `tasks.md`).
  After each section, commit, give a short status, and stop, so the user can review or
  `/compact`. If the user says to complete the whole change, work straight through and stop once
  at the end. That instruction covers that change only.
- A problem found during a change does not widen it. Assume it needs a new change, but ask the
  user before opening one: they may want only a note or an audit document.
<!-- source: crane -->
- When asked to refresh stale specs, make them describe what was implemented.
