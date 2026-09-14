# Code-graph alternatives: screening CodeGraph against code-review-graph

**Status (2026-09-14): deferred. Keeping code-review-graph.** The results are in
[`evaluations/2026-09-14-code-graph-tools/`](../evaluations/2026-09-14-code-graph-tools/README.md).
This file is the working record behind them. Reopen it only if a large-repo test (≥500 files,
tool search on) shows a clear performance gain. This run decides
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

| Surface | Tools | Schema chars | ~Tokens once loaded |
|---|---:|---:|---:|
| CRG, default | 30 | 38,630 | ~9,700 |
| CRG, `CRG_TOOLS=` the 5 tools `~/CLAUDE.md` names | 5 | 8,598 | ~2,100 |
| CodeGraph MCP | 1 (`codegraph_explore`) | 1,814 | ~450 |

**Correction (headless pilot, same day):** these are *not* paid on every request in Claude Code
2.1.270. MCP tool search is on by default from v2.1.232, so a server's tools are announced by
name only and a schema is loaded when the model calls `ToolSearch`. Measured: the first request
of each pilot run was 15,370 tokens (CRG, 30 tools) vs 15,508 (CodeGraph, 1 tool). With 29 more
tools, the CRG run's first request was actually slightly smaller. The table is the cost only once
a schema is loaded, or when `ENABLE_TOOL_SEARCH=false`.

## Headless pilot (2026-09-14): usage probe, not a valid tool comparison

**Setup:** one `claude -p` run per tool on the clone. Claude Code 2.1.270, Opus 5, subscription
(OAuth) auth. `--bare` was deliberately not used, because it accepts only an API key. Each run
had only its tool's MCP server (`--strict-mcp-config`), plus Read, Grep and Glob. It ran with
`--permission-mode dontAsk` and `--setting-sources project`, so user hooks and plugins stayed out.
Runner, configs, raw streams and graders are in `/tmp/codegraph-eval/pilot/`.

**The question:** trace `Connectome.to_network`, listing its direct calls with file:line, then
one level below that. Ground truth is an AST walk: 5 direct calls to crane code and 15 crane
callees one level down.

| Run | UTC window | API requests | Tool calls | Graph-tool calls | Input / cache write / cache read / output | API-rate cost | Score |
|---|---|---:|---|---:|---|---:|---|
| CRG | 19:31:06–19:33:12 | 10 | 27 (13 Grep, 14 Read) | **0** | 290 / 65,017 / 364,735 / 11,121 | $1.11 | L1 5/5 with lines, L2 14/15 |
| CodeGraph | 19:33:12–19:34:44 | 8 | 14 (9 Grep, 5 Read) | **0** | 226 / 40,514 / 230,234 / 7,719 | $0.72 | L1 5/5 with lines, L2 14/15 |

Each run also made one Haiku 4.5 call of about 1k tokens ($0.001).

- **Not a tool comparison.** Neither run called its graph tool: both MCP tools were deferred
  behind `ToolSearch`, and the model never searched for them. Both runs were the same Grep/Read
  baseline. The cost gap is run-to-run variance (27 vs 14 tool calls). The CodeGraph run also
  reused 8.6k cached tokens left by the CRG run just before it.
- **The question doesn't separate the tools.** Grep answered it fully, and both runs missed the
  same callee, `_to_link_matrix`.
- **Usage per run:** about 0.3–0.45M tokens, mostly cache reads, costing $0.72–1.11 at API rates.
  72 runs would come to roughly 22–31M tokens and about $50–80 at API rates. The earlier 4–15M
  token estimate was too low because it left out cache reads.
- **Plan dashboard:** the user is comparing Settings > Usage against the windows above. This
  session's own activity also counts against the same limits.

### Run 2: tools reachable (same day)

**What changed from run 1:**
- **Tool definitions loaded up front:** `ENABLE_TOOL_SEARCH=false`.
- **Each tool's own installer CLAUDE.md text** added via `--append-system-prompt`: CRG's
  `skills._CLAUDE_MD_SECTION`, and CodeGraph's `CODEGRAPH_INSTRUCTIONS_BLOCK`.
- **Server-sent guidance:** CodeGraph's MCP server also sends 5,787 characters of instructions
  when it connects; CRG's sends 189.
- **A re-export question:** every direct caller of `world_to_voxel_indices` in `src/` and
  `tests/`, then one level up for the `src/` callers. Ground truth: 8 direct callers, 12 one
  level up.
- **Timing:** both runs launched in parallel. Their tool definitions differ, so they share no
  cached prefix.

| Run | UTC window | API requests | Tool calls | First request | Input / cache write / cache read / output | API-rate cost | Score |
|---|---|---:|---|---:|---|---:|---|
| CRG | 19:41:19–19:42:20 | 6 | 17 (1 `query_graph_tool`, 10 Grep, 6 Read) | 44,330 | 162 / 76,552 / 297,402 / 4,964 | $1.04 | 8/8 direct, 12/12 one up |
| CodeGraph | 19:41:21–19:42:16 | 5 | 14 (1 `codegraph_explore`, 8 Grep, 5 Read) | 30,394 | 130 / 55,825 / 167,163 / 4,744 | $0.76 | 8/8 direct, 12/12 one up |

- **Both runs reached their tool, and neither relied on it.** Each made one graph call up front
  and then worked the answer out with Grep and Read.
- **CRG's one call failed.** `callers_of` with the bare name returned `status: ambiguous`
  (6 nodes matched), and the model never retried with a qualified name. The CRG answer is
  entirely from Grep and Read. This is the screening's ambiguity problem, now seen in real use.
- **CodeGraph's one call was useful.** It returned 19.7k characters with a blast-radius summary
  naming all three `src/` caller files and the test file. It named `_assign_endpoints` and
  `world_to_voxel`, but not `_world_to_ijk`.
- **Definition cost, now measured.** With all definitions loaded, CRG's first request was 13,936
  tokens larger than CodeGraph's. That is CRG's 30 tool definitions, net of CodeGraph's longer
  server instructions, so the chars ÷ 4 estimate of about 9,700 was low. This only applies when
  tool search is off.
- **Accuracy still doesn't separate the tools.** Grep alone answers this question too. Across the
  4 pilot runs, usage came to about $3.63 at API rates.

**Changes for the real headless runs:**
1. ~~Give each run its tool's own recommended guidance.~~ Done in run 2; it gets the tool called,
   but not trusted.
2. Add a third run with no graph tool as the baseline. Without guidance, the tool runs just
   repeat it.
3. Use multi-hop questions grep struggles with, such as calls through re-exports or on function
   parameters. The screening found exactly those misses.
4. Randomize the order and leave more than 5 minutes between runs so they don't share cache.
   Redirect stdin from `/dev/null`.

## Full headless comparison (2026-09-14, 48 runs)

This section supersedes the "Changes for the real headless runs" list above; every item on it
was applied.

**Setup:**
- **Environment:** Claude Code 2.1.270, Opus 5, subscription auth, Bash off, tool search off
  (`ENABLE_TOOL_SEARCH=false`), user settings not loaded, `dontAsk`.
- **Three setups:** no graph tool (baseline), CRG, and CodeGraph. The two graph runs got their
  tool's installer CLAUDE.md text, plus one sentence in the question telling them to use the
  tool first. For CRG that sentence names the `path::Symbol` target form. The baseline got the
  same questions without it.
- **Scale:** 4 questions × 3 setups × 4 repeats. One worker per setup ran in parallel, each
  shuffling question order per repeat with a fixed seed. Times: baseline 20:34:02–20:51:50 UTC,
  CRG 20:34:06–20:52:39, CodeGraph 20:34:11–20:53:10. No run errored.
- **Questions** (every symbol cited with its file path):
  - Q1: trace `Connectome.to_link_network` two levels deep (30 truth items).
  - Q2: callers of `world_to_voxel_indices` up to 3 levels, including re-exports (14).
  - Q3: callers of `Network.get_matrix` on a parameter receiver (8).
  - Q4: the only load-time import chain `persistence/bundle_io.py` → `connectome/workspace.py`
    → `connectome/network.py` → `connectome/exports.py` (4). This replaced a subpackage-cycle
    question that a single import grep answered.
- **Tool-use gate** (8 runs, before the matrix): 6/8 passed, and every run made successful graph
  calls. CRG Q1 reached 47% graph-first. CodeGraph Q2 reached 25%, because its one explore call
  can't cover 3 levels.

Values are medians over 4 runs; brackets give the cost range. "G-first" is the share of the
reachable truth that a graph result named before Grep, Read or Glob did.

| Q | Setup | Answer | Cost | Tool calls | Graph calls | Reads | G-first |
|---|---|---:|---|---:|---:|---:|---:|
| Q1 | baseline | 73% | $0.60 [0.56–0.67] | 14.0 | 0 | 9.0 | – |
| | CRG | 73% | $0.58 [0.53–0.74] | 14.5 | 5.0 | 7.0 | 53% |
| | CodeGraph | 73% | $0.55 [0.50–0.62] | 11.0 | 1.0 | 7.0 | 50% |
| Q2 | baseline | 100% | $0.65 [0.61–0.69] | 18.5 | 0 | 5.0 | – |
| | CRG | 100% | $0.68 [0.63–0.82] | 21.0 | 6.5 | 4.5 | none reachable |
| | CodeGraph | 100% | $0.59 [0.57–0.63] | 18.0 | 1.0 | 6.5 | 62% |
| Q3 | baseline | 100% | $0.85 [0.72–0.90] | 22.5 | 0 | 15.0 | – |
| | CRG | 100% | $1.08 [0.77–1.38] | 18.0 | 1.0 | 13.5 | 100% |
| | CodeGraph | 100% | $1.00 [0.89–1.21] | 25.5 | 1.0 | 20.0 | 100% |
| Q4 | baseline | 100% | $0.34 [0.24–0.39] | 9.5 | 0 | 1.0 | – |
| | CRG | 100% | $0.50 [0.46–0.54] | 12.5 | 2.0 | 5.0 | 67% |
| | CodeGraph | 100% | $0.52 [0.29–0.67] | 9.5 | 1.0 | 1.5 | 100% |

| Pooled | Runs | Total cost | Median cost | Mean answer | Runs with a graph call |
|---|---:|---:|---:|---:|---:|
| baseline | 16 | $9.64 | $0.62 | 93% | 0/16 |
| CRG | 16 | $11.55 | $0.65 | 93% | 16/16 |
| CodeGraph | 16 | $10.70 | $0.59 | 93% | 16/16 |

**Findings:**
- **Accuracy is identical in every cell.** On crane, Opus 5 with grep and Read already reaches
  the ceiling these questions allow. In agent runs, the graph-level accuracy differences from
  the screening (CRG missing re-export and parameter-receiver callers) never reached the
  answers, because the model double-checks with the source anyway.
- **Neither tool is reliably cheaper than grep.** CodeGraph has the lowest median on Q1 and Q2,
  but by $0.05–0.06, which is within those cells' ranges. The baseline is cheapest on Q3 and Q4.
  Q4 is the one clear gap: CRG's runs ($0.46–0.54) don't overlap the baseline's ($0.24–0.39).
  Pooled, CRG cost 20% more than the baseline and CodeGraph 11% more.
- **Graph calls didn't replace reading.** Read counts are similar, or higher (Q3 CodeGraph: 20
  vs 15).
- **Part of CRG's premium is an artifact of the setup.** With tool search off, its 30 tool
  definitions add about 14k tokens per request (measured in pilot run 2). Tool search is on by
  default and would remove most of that; the matrix did not measure it.

**Caveats:**
- **Sample size:** 4 runs per cell, so differences smaller than the ranges above are noise.
- **One small repo:** crane has 167 files, which puts CodeGraph in its one-call budget tier.
- **A disclosed treatment:** the graph runs were told to use their tool, so this measures
  whether the tool helps when used, not whether the model would choose it (in the gate, it
  mostly didn't).
- **Heuristic ground truth for Q1:** it counts only calls to names defined at most twice, and
  every setup scored 73% against it.

**What this means for a deep review.** On a repo crane's size, neither tool improves an Opus 5
agent's answers or cost over grep. The screening's case for a deep review of CodeGraph rested on
graph-level accuracy, and these runs show that doesn't carry through to agent answers here. The
remaining test worth running is the original benchmark's setting: a large repo (≥500 files,
where CodeGraph's budget rises to 2+ calls and grep gets expensive), with tool search on so
per-request cost is realistic.

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
The "about 20× lower fixed cost" argument made at screening time does not hold: deferred tool
loading makes the per-request difference negligible (see the correction above). The accuracy
results alone are enough to justify a deep review.
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

- **`config/README.md`'s MCP-versus-CLI cost rule rests on an outdated premise.** It says an MCP
  server's tool schemas are sent on every request whether used or not. In Claude Code ≥2.1.232,
  with tool search on by default, only tool names are sent until a schema is loaded (see the
  pilot). The zotero-mcp 13,448-token figure is from zotero-mcp's own docs and likely predates
  tool search. Not edited; the rule needs re-deriving, not a one-line patch.

## Raw outputs

All raw outputs are in `/tmp/codegraph-eval/out/`: tool responses, grading scripts, the coverage
database, and schema dumps. It is scratch space and will not survive a reboot, so copy anything
needed before then.
