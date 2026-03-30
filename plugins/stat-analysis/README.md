# stat-analysis

Language-agnostic statistical analysis workflows for R, Python, and Julia.

## Skills

| Skill | Command | Purpose |
|---|---|---|
| merge-data | `/merge-data` | Merge a folder of tabular files into a single analysis-ready dataframe |
| gen-data-dict | `/gen-data-dict` | Generate a BIDS-style JSON data dictionary for a merged dataframe |
| plan-analysis | `/plan-analysis` | Select the right statistical model and produce a hierarchical test sequence |
| gen-report | `/gen-report` | Scaffold a jupytext report notebook with standard sections |

## Workflow

The four skills form a linear pipeline. Each step produces output that feeds
the next — but each is independently invocable so you can enter at any stage.

```
/merge-data [folder]
    Discover, inspect, and merge tabular files → merged.tsv + merge_data.py
    ↓ review merged.tsv; confirm column names and types look right
/gen-data-dict merged.tsv
    Annotate every variable → merged_data_dictionary.json
    ↓ confirm column semantics are final before planning analysis
/plan-analysis [outcome and predictor description]
    Select statistical method → hierarchical model sequence as runnable stubs
    ↓ fit models, evaluate, refine
/gen-report [analysis title]
    Scaffold jupytext report notebook with QC plots + results sections
```

---

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/stat-analysis

# Permanent install
claude plugin install ./plugins/stat-analysis
```

## Structure

```
stat-analysis/
├── .claude-plugin/plugin.json
├── references/                         # Shared language-specific patterns (stubs)
│   ├── r-patterns.md
│   ├── python-patterns.md
│   └── julia-patterns.md
├── skills/
│   ├── merge-data/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── input-formats.md        # Supported formats, read commands, gotchas
│   │       └── merge-strategies.md     # Join types, key heuristics, wide/long detection
│   ├── gen-data-dict/
│   │   └── SKILL.md
│   ├── plan-analysis/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── test-selection.md       # Decision tree: outcome × predictors × design → method
│   │       ├── model-hierarchy.md      # Null → full model patterns and comparison tests
│   │       ├── anova-family.md         # ANOVA, ANCOVA, RM-ANOVA, MANOVA, MANCOVA
│   │       ├── regression-glm.md       # OLS, logistic, Poisson, ordinal, LME, GLMM
│   │       ├── multivariate.md         # CCA, RDA, PERMANOVA
│   │       ├── factor-analysis.md      # EFA, CFA, PCA, SEM skeleton
│   │       └── qc-metrics.md           # Shared diagnostics and assumption checks
│   └── gen-report/
│       ├── SKILL.md
│       ├── scripts/init-notebook.sh
│       └── references/
│           ├── jupytext-config.md
│           └── report-sections.md
└── agents/
    └── merge-agent/SKILL.md            # Subagent: inspects files and writes merge code
```

## Extending plan-analysis with a new statistical method

`plan-analysis` is designed so that adding a new method requires touching exactly
two files and creating one new file. No existing skill logic changes.

### Step 1: Write a method reference file

Create `skills/plan-analysis/references/<method-name>.md` using this four-section
template:

```markdown
# <Method Name>

## When to use
Describe the outcome type, predictor type, and design this method suits.
Include when NOT to use it and what to use instead.

## Key decisions to confirm with the user
List the questions that must be answered before a model formula can be written
(reference category, random effects structure, link function, etc.).

## Model hierarchy
Null → covariates → main effects → interactions.
Write as prose, then as code in R / Python / Julia.

## Assumption checks
Which checks from qc-metrics.md apply, and what to do when they fail.
```

### Step 2: Add a branch to the decision tree

Open `skills/plan-analysis/references/test-selection.md` and add a row or branch
for the new method. Specify the outcome type, predictor type, design signals, and
point to the new reference file name.

### Step 3: Nothing else

The routing skill (`SKILL.md`) loads `test-selection.md` at runtime and follows
it to the correct reference file. No changes to `SKILL.md` are needed.

---

### Graduating a method to its own skill

For methods that need a multi-turn interactive workflow beyond what a reference
file can guide (e.g., Bayesian prior elicitation, SEM path diagram specification,
ML cross-validation pipelines), create a dedicated skill instead:

```bash
bin/new-plugin skill <method-name>
# e.g. bin/new-plugin skill sem-analysis
```

In `test-selection.md`, point the relevant branch to the new skill by name:
`→ invoke /sem-analysis for structural equation modelling`

Add the new skill directory to `plugin.json` under `skills`.
