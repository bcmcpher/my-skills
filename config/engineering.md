# Engineering defaults

Defaults. A project's CLAUDE.md overrides any rule here.

## Scope and judgment

- A question is not a request for changes. Answer it; change nothing unless asked.
- A direct instruction ("do X", "update the README") is the go-ahead. Do not ask for approval
  again.
<!-- source: fwdti-plots, data-science-harness -->
- Use the simplest mechanism that solves the problem. No speculative abstraction or
  configurability. Before a first release, prefer a clean break over a compatibility shim.
<!-- source: memex, crane; Karpathy gist #2 -->
- When the codebase holds two conflicting patterns, pick one, say why, and flag the other for
  cleanup. Do not blend them.
<!-- source: Karpathy gist #7 -->
- Hand-curated files the user owns (manuscript drafts, curated configs) get paste-able output or
  a proposed diff, not direct edits.
<!-- source: fwdti-plots, emacs.d -->

## Verification and claims

- For multi-step work, state checkable success criteria before starting.
- If real data is not available to verify a feature, build a synthetic fixture. Do not defer
  the feature.
<!-- source: crane -->
- Do not over-claim. Re-measure numbers inherited from a handoff note. Check outliers before
  reporting a correlation. Verify at least once against a live run, not only a recorded fixture.
<!-- source: fwdti-plots, crane, opencite, wikiskill -->

## Long-running processes

Run any process expected to take more than a few minutes, or to outlive this session, in a named
tmux session — not as a harness background task:

```bash
mkdir -p logs
tmux new-session -d -s <project>-<task> '<cmd> 2>&1 | tee logs/<task>.log'
```

Then tell the user the session name, `tmux attach -t <project>-<task>`, and the log path. Check
progress with `tmux capture-pane -pt <name>` or the log when asked; do not poll in a loop.
HPC batch work follows the project's rules (usually SLURM scripts the user submits).
<!-- source: user 2026-10-08; fwdti-plots, prevent-ad-scripts -->

## Code graphs

A repo opts in to a code-graph tool by having its index at the repo root. Use the graph before
Grep for structural questions: who calls this, what does this change affect, which tests reach it.

- `.codegraph/` → `codegraph explore "<symbols or question>"`; also `callers`, `impact`,
  `affected <files>` (use `--json` when parsing).
- `.code-review-graph/` → `code-review-graph query callers_of|tests_for|importers_of <target>`,
  `code-review-graph impact`.
- Neither present → skip graph tools. Do not create an index; opting in is the user's decision.

Confirm a graph answer against the source before acting on it. The hooks keep both indexes
current after each edit.
<!-- source: evaluations/2026-09-14-code-graph-tools -->

## Environments

- Python: `uv venv`, `uv pip install`, `uv run`. Never bare `pip`, never the system Python.
- If the user or project names a conda environment, use it.
- Call the project interpreter by explicit path (`.venv/bin/python`, or the conda env's
  `bin/python`). Bare `python` can resolve to the harness venv `~/.claude-lsp-tools`.
  When a command also needs the env's other binaries on PATH (git-annex, apptainer), use
  `conda run -n <env> <cmd>` instead.
<!-- source: cv-cca, nb-llm-classify, pylife, crane, fwdti-plots, datalad, neuroanalytics-datasets, datalad-hpc -->

## Home directory and other repos

- Do not edit `~/.*` configuration outside `~/.claude/` unless the user asks.
- Run third-party test suites, installers and `init` commands with a throwaway home:
  `env HOME="$(mktemp -d)" <cmd>`.
- Sibling and reference repositories are read-only unless the user says otherwise.
<!-- source: my-skills, opencite, pylife, memex -->

## Plans

Write the plan first to the path plan mode gives. Then write a copy into the project, with a
descriptive kebab-case filename: its `plans/` directory, or the root if there is none.

If the project has a planning framework or spec tool (OpenSpec changes, spec-kit `specs/`, a
plugin's plans directory), its own files are the plans. Do not add a second copy.

Memories and notes cite the project copy, not `~/.claude/plans/`. Files there are not kept.
<!-- source: my-skills, cv-cca, pylife, wikiskill, emacs-d -->
