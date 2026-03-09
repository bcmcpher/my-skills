# testing

Two focused testing skills:

- **`/tdd`** — Test-first development. Write tests before the implementation exists; tests drive the design through a strict Red → Green → Refactor cycle.
- **`/retrofit-tests`** — Coverage for existing code. Systematically add unit tests to a source file you've already written, one unit at a time.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/testing

# Permanent install
claude plugin install ./plugins/testing
```

## Usage

```
/tdd <description of what to implement>
/retrofit-tests <source-file>
```

## Structure

```
testing/
├── .claude-plugin/
│   └── plugin.json
├── references/               # shared language references
│   ├── python.md
│   ├── javascript.md
│   ├── typescript.md
│   ├── rust.md
│   ├── r.md
│   └── c_cpp.md
└── skills/
    ├── tdd/
    │   └── SKILL.md
    └── retrofit-tests/
        └── SKILL.md
```
