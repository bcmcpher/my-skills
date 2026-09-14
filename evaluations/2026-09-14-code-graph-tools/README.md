# Code-graph tools for Claude Code: CodeGraph vs code-review-graph

**Date:** 2026-09-14
**Decision:** keep code-review-graph (CRG). Switching to CodeGraph is deferred until a test shows
a clear performance gain.
**Design history:** [`plans/code-graph-alternatives-eval.md`](../../plans/code-graph-alternatives-eval.md)
records every intermediate step and correction.

## Summary

Neither graph tool improved an Opus 5 agent's answers or cost over plain Grep/Read on crane, a
167-file Python repo. Across 48 headless runs, all three setups answered with the same accuracy
(93% mean). The baseline was cheapest overall ($9.64), then CodeGraph ($10.70), then CRG
($11.55). Most per-question cost differences were within run-to-run variation.

The screening found CodeGraph's graph more accurate than CRG's (re-exported callers, calls on
parameter receivers, tests for a change). None of that reached the agents' answers, because the
model double-checks against the source whether or not a graph is available.

## Versions and corpus

| Item | Value |
|---|---|
| Claude Code | 2.1.270, subscription (OAuth) auth |
| Model | Opus 5 (`--model opus`) |
| code-review-graph | 2.3.8 (latest on PyPI), with igraph 1.0.0 |
| CodeGraph | `@colbymchenry/codegraph` 1.6.0 |
| Corpus | clone of `crane` at `ed4f3c0`: 119 Python files, 50 test files, 217 commits |

## 1. Shortlist

The prompt was a blog post, "Graphify vs GitNexus vs CodeGraph". It contains no measurements,
so the shortlist comes from each project's own documentation.

| Tool | Outcome | Reason |
|---|---|---|
| GitNexus | Dropped | PolyForm Noncommercial license; no bash parsing; `analyze` writes CLAUDE.md, AGENTS.md, skills and hooks into every repo |
| Graphify | Dropped | No impact radius, test links or diff review, which are the capabilities CRG is used for here |
| CodeGraph | Tested | MIT license; CLI with `--json`; a single MCP tool; `callers`, `impact` and `affected` |

## 2. Graph-level screening (no model in the loop)

Both tools indexed the same clone. Ground truth came from an AST call index (`harness/ast_calls.py`)
and from per-test coverage (`pytest --cov-context=test`).

| Measure | CRG | CodeGraph |
|---|---|---|
| Full index time | 7.6 s | 1.8 s |
| Callers of 5 symbols, pooled over 109 callers: precision / recall | 1.00 / 0.94 | 1.00 / 0.99 |
| Tests for 5 real commits, pooled truth 62: best surface, precision / recall | `impact`: 0.41 / 0.60 | `affected --depth 1`: 0.95 / 0.68 |

**Notes:**
- **CRG's callers.** It missed callers that import through the `crane.utils` re-export, and
  `data.get_matrix(...)` calls on parameters. Given a bare symbol name it returned `ambiguous`,
  and it resolves only `path::Symbol` targets.
- **CRG's `tests_for`.** It matches tests to code by name, and found 5 of the 62 truth test
  files (precision 0.71, recall 0.08).
- **CodeGraph's `affected`.** The default test filter matched no Python tests, and depth 1 was
  chosen on the same commits it was scored on. At the default depth of 5 it scores
  0.27 / 1.00.
- **CodeGraph's other traits.** Telemetry is on by default, `.codegraph/` shows as untracked in
  git, and it has no bash parser.

## 3. Getting the agent to use the tools

Tool use has to be set up deliberately before a headless benchmark measures anything.

| Configuration | Result |
|---|---|
| Defaults: tool search on, no guidance | 0 graph calls in either run. MCP tools were deferred behind `ToolSearch`, and the model never searched for them. |
| Tool search off, plus each tool's installer CLAUDE.md text | Each run made one graph call. CRG's used a bare name, got `ambiguous`, and the model gave up on the graph. |
| Gate v1: 4 questions × 2 tools, original prompt | Graph calls in 2 of 8 runs, 0 of 4 for CRG. On Q2 the model wrote "The graph tools weren't needed". |
| Gate v2: revised prompt (one sentence pointing each graph run at its tool; `path::Symbol` targets) | All 8 runs made successful graph calls; 6 of 8 passed the reliance check |

Reliance check: of the truth items a tool's graph can reach, the share a graph result named
before any Grep/Read/Glob result did. A run passes at 50% or more.

## 4. Full comparison (48 runs)

**Setup:**
- **Scale and timing:** 4 questions × 3 setups × 4 repeats, run 20:34–20:53 UTC. One worker per
  setup ran in parallel, with question order shuffled per repeat.
- **Common to all setups:** Bash off, tool search off, user settings not loaded,
  `--permission-mode dontAsk`.
- **Graph runs:** the tool's MCP server, its installer guidance, and the revised prompt.
- **Baseline:** no MCP servers and the same question text, without the tool sentence.

**Questions** (full text in `harness/questions/`):

| Q | Task | Truth items |
|---|---|---:|
| Q1 | Trace `Connectome.to_link_network` two levels deep | 30 |
| Q2 | Callers of `world_to_voxel_indices` up to 3 levels, including re-exports | 14 |
| Q3 | Callers of `Network.get_matrix` on a parameter rather than `self` | 8 |
| Q4 | The shortest load-time import chain `persistence/bundle_io.py` → `connectome/exports.py` (3 hops) | 4 |

**Results.** Values are medians of 4 runs, with the cost range in brackets. Costs are API-rate
estimates from Claude Code; on a subscription, usage counts against plan limits instead.

| Q | Setup | Answer | Cost | Tool calls | Graph calls | Reads |
|---|---|---:|---|---:|---:|---:|
| Q1 | baseline | 73% | $0.60 [0.56–0.67] | 14.0 | 0 | 9.0 |
| | CRG | 73% | $0.58 [0.53–0.74] | 14.5 | 5.0 | 7.0 |
| | CodeGraph | 73% | $0.55 [0.50–0.62] | 11.0 | 1.0 | 7.0 |
| Q2 | baseline | 100% | $0.65 [0.61–0.69] | 18.5 | 0 | 5.0 |
| | CRG | 100% | $0.68 [0.63–0.82] | 21.0 | 6.5 | 4.5 |
| | CodeGraph | 100% | $0.59 [0.57–0.63] | 18.0 | 1.0 | 6.5 |
| Q3 | baseline | 100% | $0.85 [0.72–0.90] | 22.5 | 0 | 15.0 |
| | CRG | 100% | $1.08 [0.77–1.38] | 18.0 | 1.0 | 13.5 |
| | CodeGraph | 100% | $1.00 [0.89–1.21] | 25.5 | 1.0 | 20.0 |
| Q4 | baseline | 100% | $0.34 [0.24–0.39] | 9.5 | 0 | 1.0 |
| | CRG | 100% | $0.50 [0.46–0.54] | 12.5 | 2.0 | 5.0 |
| | CodeGraph | 100% | $0.52 [0.29–0.67] | 9.5 | 1.0 | 1.5 |

| Pooled | Total cost | Median cost | Mean answer | Total context tokens | Runs with a graph call |
|---|---:|---:|---:|---:|---:|
| baseline | $9.64 | $0.62 | 93% | 4.36M | 0/16 |
| CRG | $11.55 | $0.65 | 93% | 6.13M | 16/16 |
| CodeGraph | $10.70 | $0.59 | 93% | 5.55M | 16/16 |

Per-run data (timestamps, token classes, tool counts, answer scores) is in
[`matrix-runs.csv`](./matrix-runs.csv).

**Reading the results:**
- **Accuracy is identical in every cell.** Grep and Read already reach the ceiling these
  questions allow.
- **No setup is reliably cheaper.** CodeGraph's lead on Q1 and Q2 ($0.05–0.06) is within those
  cells' ranges. The baseline is cheapest on Q3 and Q4. The one difference outside the ranges is
  CRG costing more than the baseline on Q4.
- **Graph calls did not replace file reads.**

## 5. Context footprint

**Would CodeGraph's smaller context footprint justify revisiting the deferral? No.** Under
Claude Code's defaults, the two tools' footprints are effectively the same.

| Measurement | CRG (30 tools) | CodeGraph (1 tool) |
|---|---:|---:|
| First request, tool search **on** (the default since 2.1.232) | 15,370 tokens | 15,508 tokens |
| First request, tool search **off** | 44,330 tokens | 30,394 tokens |
| Tool definitions if every schema were loaded, chars ÷ 4 estimate | ~9,700 | ~450 |

- **With tool search on, only tool names are sent** until the model loads a schema. CRG's 30
  tools cost nothing extra on each request: its first request was actually slightly smaller.
- **The footprint gap exists only with tool search off**, as in the matrix. There, CRG's
  definitions account for about 13.9k tokens per API request, roughly 1.28M of its 6.13M
  matrix context tokens (21%). Without that overhead CRG would be about 4.84M, below
  CodeGraph's 5.55M. This is an estimate: it doesn't count the `ToolSearch` calls or loaded
  schemas that default mode would add.
- **Under the defaults, neither tool was used at all** unless the agent was told to use it.
  That's the actual cost of the reduced footprint.
- **`CRG_TOOLS` trimming to 5 tools** (about 2,100 tokens) matters only with tool search off.

## 6. Limitations

- **Sample size:** 4 runs per cell; differences smaller than the cost ranges are noise.
- **One small repo:** crane is under 500 files, so CodeGraph allows itself one explore call per
  project. The original CodeGraph benchmark used large repos (VS Code, Django, Tokio), where its
  budget rises to 2–3 calls.
- **A disclosed treatment:** the graph runs were told to use their tool, so this measures whether
  the tool helps once used, not whether the model chooses it.
- **Tool search was off in the matrix,** which inflates CRG's cost; see section 5.
- **Q1's ground truth is heuristic:** it counts only calls to names defined at most twice. Every
  setup scored 73% against it.
- **Bash was off,** unlike CodeGraph's own harness, which allows Bash and blocks its CLI.

## 7. What would change the decision

A clear performance gain means better answers, or clearly lower cost outside run-to-run
variation, on work that matters here. Tests that could show one:

1. **A large repo** (≥500 files, ideally one that also appears in CodeGraph's benchmark),
   with tool search **on** so cost reflects real use.
2. **Questions where grep is known to fail:** dynamic dispatch, callbacks, or deep transitive
   impact, graded against ground truth.
3. **Review workflows,** which this evaluation did not compare: CRG's `detect_changes` risk
   scoring against anything CodeGraph offers.

## Reproducing

`harness/` contains the benchmark code. The scripts use the absolute scratch paths from the
original run (`/tmp/codegraph-eval/...`); recreate that layout or edit the path variables.

| File | Purpose |
|---|---|
| `run.sh` | One headless run: `VARIANT=b ./run.sh <base\|crg\|cg> <Q1..Q4> <rep>` |
| `questions/Q1–Q4.txt` | Question text; `run.sh` appends the tool sentence for graph runs |
| `truth.json` | Ground-truth items per question, plus the items each tool's graph can reach |
| `gate.py` | Tool-use reliance check per run |
| `aggregate.py` | Medians per question × setup |
| `ast_calls.py` | AST call index used for callers ground truth |
| `mcp_tools.py` | Dumps an MCP server's `tools/list` |
| `mcp-*.json`, `guide-*.md` | MCP configs and each tool's installer CLAUDE.md text |
| `nocli/` | PreToolUse hook blocking both graph CLIs, for runs with Bash on (unused in the matrix) |

Raw stream-json transcripts were not committed; they were about 10 MB in scratch space.

## Cost of this evaluation

About $45 at API rates across all headless runs on 2026-09-14, of which the 48-run matrix was
$31.89. It was paid from the Claude subscription's usage limits.

## Related findings

- **igraph was pinned but not installed** in `~/.claude-lsp-tools`. Fixed with
  `bin/rebuild-tools`; CRG now runs Leiden community detection.
- **`config/README.md`'s MCP-versus-CLI cost rule rests on an outdated premise.** It says tool
  schemas are sent on every request. With tool search on by default, only names are sent until
  a schema is loaded. Not yet revised.
