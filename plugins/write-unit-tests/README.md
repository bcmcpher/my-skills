# write-unit-tests

Write comprehensive unit tests for a source code file, iterating negative-then-positive tests with full coverage of paths, edge cases, and error states.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/write-unit-tests

# Permanent install
claude plugin install ./plugins/write-unit-tests
```

## Usage

```
/write-unit-tests <source-file>
```

## Structure

```
write-unit-tests/
├── .claude-plugin/
│   └── plugin.json         # Manifest
└── skills/
    └── write-unit-tests/
        ├── SKILL.md        # Skill definition
        ├── scripts/        # Helper scripts (optional)
        ├── references/     # Reference docs (optional)
        └── assets/         # Static files (optional)
```
