# stat-analysis

Language-agnostic statistical analysis workflows for R, Python, and Julia.

## Skills

| Skill | Command | Purpose |
|---|---|---|
| merge-data | `/merge-data` | Merge input files into a single analysis-ready dataframe |
| plan-analysis | `/plan-analysis` | Select the right statistical test and QC checks for your question |
| gen-report | `/gen-report` | Scaffold a jupytext report notebook with standard sections |

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
├── references/                    # Shared language-specific patterns
│   ├── r-patterns.md
│   ├── python-patterns.md
│   └── julia-patterns.md
├── skills/
│   ├── merge-data/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── input-formats.md
│   │       └── merge-strategies.md
│   ├── plan-analysis/
│   │   ├── SKILL.md
│   │   └── references/
│   │       ├── test-selection.md
│   │       └── qc-metrics.md
│   └── gen-report/
│       ├── SKILL.md
│       ├── scripts/init-notebook.sh
│       └── references/
│           ├── jupytext-config.md
│           └── report-sections.md
└── agents/
    └── merge-agent/SKILL.md       # Subagent: inspects files and writes merge code
```
