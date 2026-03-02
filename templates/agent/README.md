# PLUGIN_NAME

DESCRIPTION

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/PLUGIN_NAME

# Permanent install
claude plugin install ./plugins/PLUGIN_NAME
```

## Usage

Describe a task that matches the agent's delegation trigger — Claude will
delegate automatically. Example triggers depend on the agent's description.

## Structure

```
PLUGIN_NAME/
├── .claude-plugin/
│   └── plugin.json         # Manifest
└── agents/
    └── AGENT_NAME/
        ├── SKILL.md        # Agent system prompt
        ├── scripts/        # Helper scripts (optional)
        ├── references/     # Reference docs (optional)
        └── assets/         # Static files (optional)
```
