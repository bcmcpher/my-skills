# PLUGIN_NAME

DESCRIPTION

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/PLUGIN_NAME

# Permanent install — via this repo's marketplace (run from the repo root)
claude plugin marketplace add .
claude plugin install PLUGIN_NAME@local        # then restart Claude Code
```

## Usage

```
/SKILL_NAME              # Invoke the skill
/SKILL_NAME [arg]        # With optional argument
```

## Structure

```
PLUGIN_NAME/
├── .claude-plugin/
│   └── plugin.json         # Manifest
└── skills/
    └── SKILL_NAME/
        ├── SKILL.md        # Skill definition
        ├── scripts/        # Helper scripts (optional)
        ├── references/     # Reference docs (optional)
        └── assets/         # Static files (optional)
```
