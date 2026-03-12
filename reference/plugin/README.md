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

```
/SKILL_NAME              # Invoke the skill
/SKILL_NAME [arg]        # With optional argument
```

Describe a task matching the agent's trigger — Claude will delegate automatically.

## Structure

```
PLUGIN_NAME/
├── .claude-plugin/
│   └── plugin.json             # Manifest
├── skills/
│   └── SKILL_NAME/
│       ├── SKILL.md            # Skill definition
│       ├── scripts/            # Helper scripts (optional)
│       ├── references/         # Reference docs (optional)
│       └── assets/             # Static files (optional)
├── agents/
│   └── AGENT_NAME/
│       ├── SKILL.md            # Agent system prompt
│       ├── scripts/            # Helper scripts (optional)
│       ├── references/         # Reference docs (optional)
│       └── assets/             # Static files (optional)
├── .lsp.json                   # LSP server config (optional)
├── hooks/hooks.json            # Event hooks (optional)
└── .mcp.json                   # MCP server config (optional)
```
