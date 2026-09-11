# datalad-cli

Claude Code plugin that routes data processing and file changes through DataLad for
provenance tracking. Follows YODA principles for reproducible local analysis projects.

## Skills

| Skill | Slash command | Trigger |
|---|---|---|
| `datalad-init` | `/datalad-init` | Explicit: creating a new dataset or YODA layout |
| `datalad-stamped-assess` | `/datalad-stamped-assess` | Explicit: grading a dataset against the STAMPED reproducibility principles (add `--plan` for remediation) |
| `datalad-run` | `/datalad-run` | Auto: executing scripts/pipelines that produce output files |
| `datalad-save` | `/datalad-save` | Auto: saving code changes inside a DataLad dataset |
| `datalad-container-run` | `/datalad-container-run` | Auto: running commands inside Singularity/Apptainer/Docker containers |
| `datalad-status` | `/datalad-status` | Auto: checking dataset state |
| `datalad-diff` | `/datalad-diff` | Auto: comparing dataset versions |
| `datalad-clone` | `/datalad-clone` | Auto: obtaining a copy of a dataset |
| `datalad-get` | `/datalad-get` | Auto: retrieving annexed file content |
| `datalad-push` | `/datalad-push` | Auto: pushing dataset to a sibling |
| `datalad-update` | `/datalad-update` | Auto: updating from a sibling |
| `datalad-siblings` | `/datalad-siblings` | Auto: configuring remote siblings |
| `datalad-subdatasets` | `/datalad-subdatasets` | Auto: managing nested subdatasets |
| `datalad-untrack` | `/datalad-untrack` | Auto: dropping content or removing files |
| `datalad-addurls` | `/datalad-addurls` | Auto: bulk-adding files from URLs |
| `datalad-configuration` | `/datalad-configuration` | Explicit: dataset configuration |
| `datalad-export` | `/datalad-export` | Explicit: exporting to archive or Figshare |
| `datalad-log` | `/datalad-log` | Auto: browsing run history and provenance |
| `datalad-credentials` | `/datalad-credentials` | Auto: setting up authentication credentials |
| `datalad-fsck` | `/datalad-fsck` | Auto: checking annex integrity for missing or corrupt content |

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/datalad-cli

# Permanent install — via this repo's marketplace (run from the repo root)
claude plugin marketplace add .
claude plugin install datalad-cli@local        # then restart Claude Code
```

## Quick workflow

```bash
# 1. Create a YODA dataset
/datalad-init my-analysis

# 2. Add code, link inputs as subdatasets
# (put scripts in code/, link data via datalad clone)

# 3. Run analysis with provenance
/datalad-run python code/analysis.py

# 4. Save code changes
/datalad-save "add preprocessing step to analysis script"
```

## Reproducibility principles

YODA gives the concrete dataset layout this plugin enforces, and is the **Self-containment +
Modularity** core of the broader **STAMPED** framework (Self-containment, Tracking,
Actionability, Modularity, Portability, Ephemerality, Distributability).

YODA layout, enforced on init:

- **P1**: Input data linked as subdatasets (`inputs/`), not copied
- **P2**: Data origins recorded via `datalad download-url` or `datalad clone`
- **P3**: `inputs/` treated as read-only; all results go to `outputs/`

To grade a dataset across all seven STAMPED principles — and get an ordered plan of fixes
mapped to the skills above — run `/datalad-stamped-assess [path] --plan`. See
`references/stamped-principles.md` for the full checklist and `references/yoda-layout.md` for
the YODA layout detail.

## Relationship to the K-Dense `datalad` skill

`K-Dense-AI/scientific-agent-skills` ships a [`datalad`
skill](https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/datalad) covering
the same tool. The two are deliberately different shapes, and neither supersedes the other:

| | This plugin | The K-Dense skill |
|---|---|---|
| Shape | 20 skills, one per command, each auto-invocable on its own trigger | One agent-facing decision skill plus three reference files |
| Optimized for | Driving DataLad from a session, command by command | Deciding *whether and how* to reach for DataLad at all |
| Ships | Hooks, a STAMPED assessment skill, per-command references | A failure-mode table, data-access / provenance / publishing references |

Its author wrote it independently, and credited this plugin as MIT-licensed orientation
material in [PR #227](https://github.com/K-Dense-AI/scientific-agent-skills/pull/227). The
STAMPED property→command mapping went the other way: it originates in
`references/stamped-principles.md` here and was contributed upstream.

Because the two overlap on facts, a correction to one is usually a correction to both — worth
checking the other before assuming a divergence is intentional.

## Auto-checkpoint hook

The plugin installs a `Stop` hook that runs after every Claude turn. If the current
directory is inside a DataLad dataset and there are unsaved changes, it automatically
commits them:

```
[datalad] checkpoint 2026-03-12T14:05:22Z: code/analysis.py outputs/result.csv
```

**Opt out** for a session:
```bash
DATALAD_AUTOSAVE=0 claude --plugin-dir ./plugins/datalad-cli
```

The hook exits silently (no error, no commit) when:
- `datalad` is not on `$PATH`
- The cwd is not inside a DataLad dataset
- `DATALAD_AUTOSAVE=0` is set
- There are no modified or untracked files

**Checkpoint commits in run history**: checkpoint commits appear in `git log` alongside
`datalad run` provenance records. (There is no `datalad log` command — use `git log`, and
`datalad rerun --report <sha>` to inspect a single run record without re-executing it.)

The `[datalad] checkpoint …` line above is what the hook prints to the terminal. The *commit*
it writes is subject-prefixed `Auto-checkpoint`, so the two are separated like this:

```bash
git log --oneline --grep='\[DATALAD RUNCMD\]'   # run records only
git log --oneline --grep='^Auto-checkpoint'      # hook checkpoints only
```

## Structure

```
datalad-cli/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       └── datalad-checkpoint.sh
├── references/                        ← shared across all skills
│   ├── yoda-layout.md
│   ├── subdataset-patterns.md
│   ├── siblings-and-remotes.md
│   ├── annex-content-states.md
│   └── troubleshooting.md
└── skills/
    ├── datalad-init/SKILL.md
    ├── datalad-run/
    │   ├── SKILL.md
    │   └── references/run-command.md
    ├── datalad-save/SKILL.md
    ├── datalad-container-run/
    │   ├── SKILL.md
    │   └── references/container-run.md
    ├── datalad-log/SKILL.md
    ├── datalad-credentials/SKILL.md
    └── [... 12 more skill directories]
```
