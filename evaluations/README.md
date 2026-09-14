# evaluations/

Measured comparisons of tools and configurations for this Claude Code setup. Each evaluation has
its own dated directory. The directory holds a results `README.md` that states the decision, the
data behind it, and what would change it, plus enough of the harness to rerun it.

Design docs for work not yet done belong in `plans/`. An evaluation lands here once it has
produced a result, even when the result is to change nothing.

| Evaluation | Date | Decision | Revisit when |
|---|---|---|---|
| [code-graph-tools](./2026-09-14-code-graph-tools/) | 2026-09-14 | Keep code-review-graph; CodeGraph deferred. No accuracy or cost gain over grep on a 167-file repo. | A large-repo test (≥500 files, tool search on) shows a clear gain |
