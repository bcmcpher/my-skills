# Project Type: Data Analysis

## Description

A reproducible research or analytical project producing models, figures, reports, and
other derivative outputs for distribution. Emphasis on data lineage, pipeline
reproducibility, and clear separation between raw inputs and processed outputs.

## Primary language

Python (most common) or R. Ask the user. Both may coexist in a single project.

---

## Directory scaffold

```
<name>/
├── data/
│   ├── raw/              # read-only source data — never modified by pipeline
│   └── processed/        # pipeline outputs; can be regenerated
├── notebooks/            # exploratory analysis; NOT pipeline steps
├── src/
│   └── <name>/           # importable analysis library / shared utilities
├── models/               # trained model artifacts
├── figures/              # generated plots and visualizations
├── reports/              # final outputs: LaTeX, Quarto, Rmd, or Markdown
├── .gitignore
├── README.md
├── Makefile              # or pipeline stub (see below)
└── pyproject.toml        # or renv.lock for R
```

---

## Essential files

### README.md

```markdown
# <name>

<description>

## Data

<!-- Describe source datasets, access method, and any licensing constraints. -->

**Source:** <dataset name / URL / DOI>
**Access:** <public download / DVC pull / DataLad get / institutional access>
**License:** <data license>

## Reproducing results

```bash
# 1. Set up environment
/env-check

# 2. Get data
# e.g., datalad get data/raw/ OR dvc pull OR wget ...

# 3. Run pipeline
make all

# 4. View outputs
# figures/ and reports/
```

## Project structure

| Directory | Contents |
|---|---|
| `data/raw/` | Unmodified source data |
| `data/processed/` | Pipeline outputs |
| `notebooks/` | Exploratory analysis |
| `src/<name>/` | Analysis library |
| `models/` | Trained model files |
| `figures/` | Generated plots |
| `reports/` | Final reports |

## Citation

<!-- If this analysis is published, add citation here. -->
```

### Makefile

```makefile
.PHONY: all data figures reports clean

all: figures reports

data:
	# retrieve or preprocess raw data
	# e.g., python src/<name>/fetch_data.py

figures: data
	# generate all figures
	# e.g., python src/<name>/make_figures.py

reports: figures
	# render final reports
	# e.g., quarto render reports/main.qmd

clean:
	rm -rf data/processed/ figures/ models/
	find . -name "*.pyc" -delete
```

---

## .gitignore additions

Beyond the standard language entries from `references/git.md`, add:

```
# Large data files — track with DataLad or DVC instead
data/raw/
models/*.pkl
models/*.h5
models/*.pt
models/*.onnx

# Notebook checkpoints
.ipynb_checkpoints/
*/.ipynb_checkpoints/

# Generated outputs (can be reproduced)
figures/
reports/_output/

# R
.Rhistory
.RData
```

**Note on `data/raw/`**: If datasets are small enough to commit directly, remove this
entry. For large or proprietary datasets, use DataLad or DVC — see the DataLad section
below.

---

## DataLad consideration

DataLad is the preferred tool for managing versioned data files in analysis projects,
especially when:

- Raw data is too large to commit to git directly
- Data has a canonical remote source (DOI, URL, institutional store)
- Multiple collaborators need to `datalad get` specific files on demand
- Binary derivatives (models, figures) need provenance tracking via `datalad run`

If the `datalad-cli` plugin is installed, Claude can use DataLad skills throughout this
project. Recommend the user initialize the project as a DataLad dataset:

```bash
# Instead of plain git init, use:
datalad create <name>
cd <name>

# Register a remote data source
datalad addurls <urls-file> --path data/raw/{filename}

# Record pipeline runs with provenance
datalad run -m "Generate figures" make figures
```

The `datalad-cli` plugin provides skills for `datalad-init`, `datalad-run`,
`datalad-save`, `datalad-get`, `datalad-push`, and others. Reference these when
suggesting data management steps.

---

## CLAUDE.md template

```markdown
## Project

**Type:** data-analysis
**Language:** <Python | R | Python + R>
**Description:** <description>

## Data

**Source:** <dataset name / URL / DOI — where does the raw data come from?>
**Access:** <how to retrieve it: DataLad get / DVC pull / download URL / institutional>
**License:** <data license or access restrictions>
**Size:** <approximate total size>

## Pipeline

| Stage | Command | Input | Output |
|---|---|---|---|
| Fetch data | `make data` | — | `data/raw/` |
| Preprocess | `<command>` | `data/raw/` | `data/processed/` |
| Train / fit | `<command>` | `data/processed/` | `models/` |
| Figures | `make figures` | `data/processed/`, `models/` | `figures/` |
| Reports | `make reports` | `figures/`, `data/processed/` | `reports/` |

## Commands

| Task | Command |
|---|---|
| Full pipeline | `make all` |
| Data only | `make data` |
| Figures only | `make figures` |
| Reports only | `make reports` |
| Clean outputs | `make clean` |
| Run tests | `<test command>` |

## Reproducibility

- Random seed: `<seed value or "not applicable">`
- Platform notes: `<any OS or hardware dependencies>`
- DataLad: `<"initialized" or "not used">`

## Analysis goals

<!-- Describe what questions this analysis is trying to answer. -->

<primary research question or analysis objective>

## Output locations

- Figures: `figures/` — <file naming convention>
- Reports: `reports/` — <report format: Quarto / LaTeX / Rmd / Markdown>
- Models: `models/` — <serialization format: pickle / joblib / .pt / .h5>
```

---

## Recommended Claude configuration

### LSP

**Useful** for the `src/` library code. Less critical for notebooks (exploratory).
Set up pyright for Python or the R language server for R.

### Hooks

**Light touch.** `ruff format` on Python files in `src/` is appropriate. Avoid
aggressive linting hooks on notebook files — analysis code is exploratory.

See `references/claude-config/hooks.md` for patterns.

### MCP

- **DataLad** (`datalad-cli` plugin): for data versioning and provenance. Strongly
  recommended. Without it, large data files must be managed manually.
- **GitHub MCP**: if outputs or analysis code will be shared via GitHub.

### Recommended agents

**analysis-assistant**

```yaml
name: analysis-assistant
description: >
  Assists with analysis tasks: interprets results, suggests statistical approaches,
  helps debug pipeline steps, and explains model outputs. Aware of DataLad tools for
  data management. Use when discussing analytical choices, asking "why did this
  result look like X", or requesting statistical methodology guidance.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
maxTurns: 20
```

Body: Load `CLAUDE.md` sections for pipeline, data, and analysis goals. Help interpret
results in context of the stated objectives. When suggesting data operations, prefer
`datalad run` over bare shell commands so pipeline steps are recorded with provenance.
DataLad tools are available via the `datalad-cli` plugin if installed: use
`datalad save`, `datalad run`, `datalad get`, and `datalad push` as appropriate.

---

**report-drafter**

```yaml
name: report-drafter
description: >
  Drafts prose sections of a report or paper given a figure, table, or analysis
  result. Use when asked to "write up these results", "draft the methods section",
  or "describe this figure".
tools: Read, Glob, Write, Edit
model: inherit
permissionMode: default
maxTurns: 10
```

Body: Read the target figure caption or analysis output. Load relevant context from
`CLAUDE.md` (analysis goals, data description). Draft clear, precise prose suitable
for the output format (Quarto / LaTeX / Markdown). Do not fabricate statistics —
report only what is present in the inputs.

---

**pipeline-debugger**

```yaml
name: pipeline-debugger
description: >
  Diagnoses failures in the analysis pipeline: missing data files, broken
  dependencies, environment mismatches, or unexpected outputs. DataLad-aware.
  Use when a pipeline step fails or produces unexpected results.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
maxTurns: 20
```

Body: Read the error output and the relevant pipeline step. Check for missing input
files (offer `datalad get` if DataLad is initialized), environment issues, or logic
errors. Do not modify source data. Propose targeted fixes to `src/` or `Makefile`.

### Recommended local skills

None required — agents above cover primary workflows.
