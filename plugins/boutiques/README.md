# boutiques

Generate a [Boutiques](https://boutiques.github.io/) schema-version 0.5 JSON
descriptor for any CLI tool by inspecting its `--help` output.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/boutiques

# Permanent install
claude plugin install ./plugins/boutiques
```

## Usage

```
/boutiques <command>               # Describe a top-level command
/boutiques <command> <subcommand>  # Describe a specific subcommand
```

Examples:

```
/boutiques bet
/boutiques git commit
/boutiques fslreorient2std
```

Claude will:
1. Run `<command> --version` and `<command> --help` (falling back to `-h`)
2. Parse flags, positional arguments, and infer Boutiques types
3. Ask you where to save the `.json` file before writing anything
4. Write a valid Boutiques 0.5 descriptor to that path

## Structure

```
boutiques/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── boutiques/
        ├── SKILL.md
        └── references/
            └── boutiques-schema.md   # Full field reference, loaded on demand
```

## Notes

- One descriptor per command/subcommand pair. For tools with many subcommands,
  invoke the skill once per subcommand.
- Container image info (`docker`/`singularity`) is not auto-detected; add it
  manually after generation if needed.
- Validate the output with `bosh validate <descriptor.json>` if you have the
  Boutiques Python package installed (`pip install boutiques`).
