# modular-analysis

Claude Code plugin for structuring repeated analyses — any procedure you run for every
combination of outcome × predictor × condition × ROI × cohort — around a five-layer
architecture:

```
constants → data loading → atomic functions → output functions → orchestrator (run_one)
```

Language-agnostic. The layers are a design discipline, not a framework: they apply equally
to R, Python, Julia, MATLAB, or shell.

## Skills

| Skill | Slash command | Trigger |
|---|---|---|
| `analysis-plan` | `/analysis-plan` | Explicit: designing a new repeated analysis from scratch |
| `analysis-refactor` | `/analysis-refactor` | Explicit: restructuring an existing linear or copy-paste script |

Each skill points at the other when the user is in the wrong one — `/analysis-plan` for a
blank page, `/analysis-refactor` for a script that already works but has grown unmanageable.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/modular-analysis

# Permanent install — via this repo's marketplace (run from the repo root)
claude plugin marketplace add .
claude plugin install modular-analysis@local        # then restart Claude Code
```

## The five layers

| Layer | Holds | Rule |
|---|---|---|
| Constants | paths, dimension lists, thresholds, seeds | named once at the top; never buried in a function |
| Data loading | everything that reads from disk or network | returns a clean in-memory structure; no analysis |
| Atomic functions | one statistical or computational step each | pure — return a value, touch nothing outside their scope |
| Output functions | tables, figures, serialized results | the only functions with side effects; never construct their own paths |
| Orchestrator | `run_one(...)` plus the loop over dimensions | the only function that knows the output path, and passes it in |

The method that makes it work is ordering, not vocabulary: **write the orchestrator
pseudocode before implementing anything.** Naming what each step must return forces the
function boundaries to fall in the right places, instead of discovering them halfway
through an implementation.

## Quick workflow

```bash
# Starting from nothing
/analysis-plan run a mixed-effects model for each of 4 outcomes across 7 ROIs

# Starting from a script that got out of hand
/analysis-refactor scripts/analysis.R
```

## Structure

```
modular-analysis/
├── .claude-plugin/
│   └── plugin.json
├── evals/
│   └── evals.json                     ← skill-creator benchmark definitions
├── references/                        ← shared across both skills
│   └── research-analysis-guidance.md
└── skills/
    ├── analysis-plan/SKILL.md
    └── analysis-refactor/SKILL.md
```

`references/research-analysis-guidance.md` is loaded on demand by both skills; it carries the
longer material on naming conventions, output layout, and the design rules to hold throughout.
