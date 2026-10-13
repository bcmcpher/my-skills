# Git workflow

Defaults. A project's CLAUDE.md or `.claude/rules/` overrides any rule here.

## Branches and commits

- Work on a branch named after the change, or follow the repo's own `type/slug` convention.
  Experimental or risky edits stay off the default branch until the user says otherwise.
<!-- source: crane, datalad-hpc, fwdti-plots, prevent-ad-scripts -->
- Commit when a task group or logical step is complete, not only at the end. Put an unrelated
  fix in its own commit.
<!-- source: data-science-harness, my-skills -->
- Commit source, not its outputs: no data, results, `dev-data/` or talk material. If a commit
  would add such files, stop and ask.
<!-- source: fwdti-plots, pylife, crane, data-science-harness -->
- Move tracked files with `git mv`; check with `git ls-files --error-unmatch <path>`.
- Match the commit-message style in `git log`. In a repo with no history, use a plain imperative
  sentence-case subject. Follow the repo's author and co-author conventions.

## Reviews

Before a merge, run `/code-review` on the branch.

Also recommend a mid-change review — do not run it unprompted — at a commit boundary when any of
these holds since the branch point or the last review:

- the diff is about 400 changed lines or more (`git diff --shortstat <base>...HEAD`);
  review effectiveness falls past 200–400 lines;
- about half of the change's tasks are checked off and the diff is not trivial;
- the change touched shared code: a public API, a schema, a CLI interface, or a module other
  code imports;
- the next step builds on the current code (a refactor, or a new layer on top).

After a review, mark the point with a local ref that is never pushed:
`git update-ref refs/review/<branch> HEAD`. The next review covers the diff from that ref.

## Close-out order

When a change is done: `/code-review` → fix findings → archive the spec with its tool, if any →
commit → merge with `--no-ff` → push (only when asked; see below) → delete the branch. Pause for the user between changes,
not between task groups inside one change.
<!-- source: crane, datalad-hpc, data-science-harness -->

## Outward-facing actions

- Push, open a PR, or post an issue or comment only when the user asks for it at that moment.
  Approval of a plan is not approval to publish. A project may grant a standing authorization in
  its own CLAUDE.md or memory.
- Before anything public, show its full text verbatim in a fenced block, especially any
  @-mention of a person.
<!-- source: neuroanalytics-datasets, opencite, my-skills, k-dense -->

## Handoff

When the user says to save, stop, or leave work for later: commit the work in progress and write
a resume note (what is done, what is next, open questions) at once. Do no further work first.
<!-- source: data-science-harness, memex-vault, pylife -->
