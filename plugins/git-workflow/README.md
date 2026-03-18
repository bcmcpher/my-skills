# git-workflow

DESCRIPTION

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/git-workflow

# Permanent install
claude plugin install ./plugins/git-workflow
```

## Usage

```
/git-workflow              # Invoke the skill
/git-workflow [arg]        # With optional argument
```

## Structure

```
git-workflow/
├── .claude-plugin/
│   └── plugin.json         # Manifest
└── skills/
    └── git-workflow/
        ├── SKILL.md        # Skill definition
        ├── scripts/        # Helper scripts (optional)
        ├── references/     # Reference docs (optional)
        └── assets/         # Static files (optional)
```
