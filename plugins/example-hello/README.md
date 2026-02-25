# example-hello

A minimal working example of a Claude Code plugin with one skill and one subagent.

## What's included

| Component | Trigger | Description |
|-----------|---------|-------------|
| Skill: `hello` | `/hello [name]` | Greets the user and summarizes the current project |
| Agent: `greeter` | "cheer me up", "pep talk" | Motivational subagent that reads the project and gives specific encouragement |

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/example-hello

# Permanent install
claude plugin install ./plugins/example-hello
```

## Usage

```
/hello                  # Greet with project context
/hello Alice            # Greet Alice specifically
"give me a pep talk"    # Delegates to the greeter subagent
```

## Structure

```
example-hello/
├── .claude-plugin/
│   └── plugin.json     # Manifest wiring skills + agents together
├── skills/
│   └── hello/
│       └── SKILL.md    # /hello skill definition
├── agents/
│   └── greeter/
│       └── SKILL.md    # greeter subagent system prompt
└── README.md
```
