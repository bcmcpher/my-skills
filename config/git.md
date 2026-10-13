# Git workflow

Defaults. A project's CLAUDE.md or `.claude/rules/` overrides any rule here.

## Branches and commits

- Build every new feature on its own branch, never directly on the default branch, whatever
  drives it: an OpenSpec change, a plan, or an ordinary request. Create the branch before the
  first commit. Name it `change/<change-id>` for an OpenSpec change and `plan/<plan-slug>` for
  a plan, unless the repo has its own `type/slug` convention.
- Plan ticks and "As built" notes are committed on the same branch as the code.
<!-- source: crane, datalad-hpc, fwdti-plots, prevent-ad-scripts, live CLAUDE.md branch section -->
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
commit → merge with `--no-ff` (ask first) → push (only when asked; see below) → delete the branch. Pause for the user between changes.
In a repo with a spec tool, also pause inside a change (see `specs.md`).
<!-- source: crane, datalad-hpc, data-science-harness -->

## Outward-facing actions

- Push, open a PR, or post an issue or comment only when the user asks for it at that moment.
  Approval of a plan is not approval to publish. A project may grant a standing authorization in
  its own CLAUDE.md or memory.
- Before anything public, show its full text verbatim in a fenced block, especially any
  @-mention of a person. Use a 4-backtick fence when the text itself contains ``` fences.
- On a repo the user does not own, comments, reviews and issues are drafts: show the text and
  let the user post it.
<!-- source: neuroanalytics-datasets, opencite, my-skills, k-dense -->

## Handoff

When the user says to save, stop, or leave work for later: commit the work in progress and write
a resume note (what is done, what is next, open questions) at once. Do no further work first.
<!-- source: data-science-harness, memex-vault, pylife -->
