# Code-graph alternatives: screening CodeGraph against code-review-graph

**Status (2026-09-14): screening done — deep review warranted, not started.** This run decides
only whether CodeGraph deserves a deep review. It does not decide a switch. Step 5 of the
screening plan (headless exploration runs, which cost API spend) was not run.

## Why CodeGraph, and not the other two

The prompt was the post "Graphify vs GitNexus vs CodeGraph". It has no repo links, no benchmarks
and no hands-on testing, so the shortlist comes from each project's own README.

- **GitNexus — dropped.** PolyForm Noncommercial license; 17 MCP tools; native LadybugDB and
  onnxruntime deps; no bash. `gitnexus analyze` writes CLAUDE.md, AGENTS.md, skills and hooks into
  every repo, the same objection `config/README.md` raises against `code-review-graph install`.
- **Graphify — not a substitute.** It has no impact radius, no test links and no diff review,
  which are the tools `~/CLAUDE.md` prescribes. What sets it apart is putting docs, papers and
  code in one graph. That is relevant to the Obsidian-memory plan, not to code review.
- **CodeGraph** (`@colbymchenry/codegraph` 1.6.0, MIT): CLI with `--json`, one MCP tool, `callers`,
  `impact`, and `affected` (tests reached through imports).

## Setup

- Corpus: a clone of `~/Projects/crane/crane` at `ed4f3c0` in `/tmp/codegraph-eval/crane`: 119 py
  files, 50 test files, both tools indexing the identical tree. The user's crane checkout was never
  written to.
- CodeGraph installed to `/tmp/codegraph-eval` (not `~/.claude-node-tools`, not `config/tools/`).
  `codegraph install` was never run. All runs used a sandbox `HOME`, `CODEGRAPH_NO_DAEMON=1`, and
  `CODEGRAPH_TELEMETRY=0` after the first two commands.
- CRG 2.3.8 from `~/.claude-lsp-tools`, rebuilt in the clone under the same sandbox `HOME`.

| | CodeGraph | CRG |
|---|---:|---:|
| Full index, wall time | 1.8 s | 7.6 s |
| Nodes / edges | 4,310 / 11,912 | 3,222 / 26,826 |
| Files | 167 (119 py + 48 yaml) | 168 |

## Results

### Callers of a symbol

Ground truth: an AST call index over `src/`, `tests/` and `examples/` (`/tmp/codegraph-eval/ast_calls.py`).
Targets are names defined exactly once, so a name match is a real call. The unit is
(file, enclosing function); module-level call sites are excluded from both tools' scores. Pyright
could not serve as a cross-check: the LSP workspace is my-skills, so it found only same-file
references.

| Target (fan-in) | CRG P / R | CodeGraph P / R |
|---|---|---|
| `values_equal` (2) | 1.00 / 1.00 | 1.00 / 0.50 — missed the recursive self-call |
| `EdgePairs.require_identity` (3) | 1.00 / 1.00 | 1.00 / 1.00 |
| `world_to_voxel_indices` (8) | 1.00 / 0.62 — missed 3 callers importing via the `crane.utils` re-export | 1.00 / 1.00 |
| `NetworkGroup.compute_subject_delta` (29) | 1.00 / 1.00 | 1.00 / 1.00 |
| `Network.get_matrix` (67) | 1.00 / 0.96 — missed 3 `data.get_matrix(...)` calls on parameter receivers | 1.00 / 1.00 |
| **Pooled (109 callers)** | **1.00 / 0.94** | **1.00 / 0.99** |

Two surface differences affect real use:
- **CRG needed a second query on 3 of the 5 targets.** Bare names returned `status: ambiguous`
  because test functions also matched. Scores above are after re-querying with the qualified name,
  as the MCP client would.
- **CodeGraph adds file-level import nodes to its callers list.** For `world_to_voxel_indices` that
  was 5 extra entries such as `assignment.py`. They are excluded from the function-level P above,
  but a model would have to filter them.

### Tests for a change

The changes are 5 real crane commits: `14a3756`, `5aecf06`, `b2bf9bd`, `663a13f` and `c13b12c`.
Each tool got the commit's changed `src/` files, evaluated against the graph at HEAD. Ground
truth is from `pytest --cov-context=test` (full suite, 65 s, exit 0). A test file counts if it
executes a line of a changed file that isn't also run at import time. The unit is the test file.

| Surface | Pooled P | Pooled R | Predicted / truth |
|---|---:|---:|---:|
| CRG `query tests_for <file>` | 0.71 | **0.08** | 7 / 62 |
| CRG `impact --files`, test files in the result | 0.41 | 0.60 | 90 / 62 |
| CodeGraph `affected --filter 'tests/*.py' --depth 1` | **0.95** | **0.68** | 44 / 62 |
| CodeGraph `affected … --depth 2` | 0.39 | 1.00 | 160 / 62 |
| CodeGraph `affected … --depth 5` (default depth) | 0.27 | 1.00 | 226 / 62 |

Per-commit numbers are in `/tmp/codegraph-eval/out/grade-affected.txt`.

- **CRG `tests_for` confirms the known `TESTED_BY` gap.** It is name-heuristic and finds about
  1 test file in 12.
- **CodeGraph's defaults don't work for Python.** The default test filter matched no crane test
  file (0 results on every commit), and `--filter 'tests/**/*.py'` also matched nothing. Only
  `tests/*.py` worked. At the default depth of 5 it flags 43–47 of 50 test files for any change.
- **The depth-1 advantage is optimistic.** Depth 1 was chosen by looking at these same 5 commits.

### Fixed context cost (MCP tool schemas)

Schemas came from each server's `tools/list` over stdio (`/tmp/codegraph-eval/mcp_tools.py`).
Token counts are **chars ÷ 4 estimates**: no tokenizer or API key was available. The zotero table
in `config/README.md` is zotero-mcp's published figure, not a local method, so there was nothing
to reuse.

| Surface | Tools | Schema chars | ~Tokens per request |
|---|---:|---:|---:|
| CRG, default | 30 | 38,630 | ~9,700 |
| CRG, `CRG_TOOLS=` the 5 tools `~/CLAUDE.md` names | 5 | 8,598 | ~2,100 |
| CodeGraph MCP | 1 (`codegraph_explore`) | 1,814 | ~450 |

Trimming CRG with `CRG_TOOLS` is available today, independent of any switch.

## Operational findings about CodeGraph

- **Telemetry is on by default.** It ships an anonymous machine UUID and command counts, per
  `TELEMETRY.md`. The first `init` printed a notice and queued `init` and `status` events. No
  `index` event was in the queue, so whether one was already sent can't be confirmed. The MCP
  server also checks GitHub for updates daily unless `DO_NOT_TRACK=1`.
- **`.codegraph/` shows as untracked** (`?? .codegraph/`): only the db inside is ignored. In a
  real repo that dirties `git status`, unlike CRG's self-ignoring directory.
- **No bash parsing.** crane's shell scripts and all of my-skills' hooks are invisible to it.
- **No line-level diff review.** There is nothing like CRG `detect_changes` risk scoring;
  `affected` is file-level only. That surface was not compared.
- **The background daemon is the default.** It was disabled here and never exercised.

## Verdict: deep review warranted

On one Python repo, CodeGraph matched or beat CRG on callers (R 0.99 vs 0.94). The misses it
avoided are the ones that matter: re-exports and calls on parameter receivers. On tests for a
change it was clearly better at depth 1 (P 0.95 / R 0.68 vs CRG's best surface at 0.41 / 0.60).
Its fixed cost is about 20× lower than CRG's default. That is enough to justify a deep review.
It isn't enough to act on, given the limits below.

### What a deep review still has to verify

1. **Held-out items.** Depth and filter were tuned on these same 5 commits; re-test on fresh
   commits and fresh targets.
2. **A second, different corpus.** `claude/fwdti-plots` (py/js/R, 77 commits) and a repo the user
   did not write.
3. **In-session behaviour.** The skipped step 5: does `codegraph_explore` cut tool calls and tokens
   on real questions, as its README claims? This needs API spend, so ask first.
4. **Daemon and watcher.** Resource use and correctness over a full editing session, and how they
   interact with the `graph-update.sh` opt-in gate.
5. **Bash gap.** Is CRG still needed alongside it for shell-heavy repos? Running two graph tools
   may cost more than either alone.
6. **Wiring without `codegraph install`.** A CLI skill versus the single MCP tool, telemetry off
   made persistent, and `.codegraph/` git hygiene.
7. **Maturity.** Release cadence, breaking changes across 1.x, and issue response.

## Side findings, not acted on

- **igraph was pinned in `config/tools/python-lock.txt` but not installed.** Commit `763f11f` never
  reached the live env, and CRG builds logged "igraph not available, using file-based community
  detection". *Fixed 2026-09-14* by `bin/rebuild-tools`; `--check` is now green and CRG runs Leiden.
- **The my-skills graph was stale, not just incomplete.** It held 2 files and 18 nodes. A full
  `code-review-graph build` on 2026-09-14 produced 19 files and 42 nodes, so the hooks' incremental
  updates had not been picking up most files. Whether the extensionless `bin/*` scripts are now
  included was not checked.
- **Five opted-in graphs are empty.** `~/Projects/nipoppy` and `nipoppy/giga-connectome` are not
  git repos, and `cns-calgary-2026`, `ohbm-2026` and `k-dense/scientific-agent-skills` are also
  empty. They look like opt-ins at parent directories.

## Raw outputs

All raw outputs are in `/tmp/codegraph-eval/out/`: tool responses, grading scripts, the coverage
database, and schema dumps. It is scratch space and will not survive a reboot, so copy anything
needed before then.
