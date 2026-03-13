# Project Type: Coding Tool / Package

## Description

A library, CLI, or service intended for programmatic use, potentially with external
contributors. Focus on code quality, API design, testing, documentation, and release
management.

## Primary language

None fixed — ask the user. Python, TypeScript, Rust, and Go are common.

---

## Directory scaffold

```
<name>/
├── src/
│   └── <name>/           # Python: package dir; adjust for other languages
├── tests/
├── docs/
├── .github/
│   ├── workflows/
│   │   ├── test.yml
│   │   └── publish.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── .gitignore
├── .editorconfig
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── <manifest>            # pyproject.toml / Cargo.toml / go.mod / package.json
```

---

## Essential files

### README.md

```markdown
# <name>

<description>

## Installation

```bash
# e.g. pip install <name>
```

## Usage

```python
# minimal usage example
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
```

### CONTRIBUTING.md

```markdown
# Contributing to <name>

## Development setup

```bash
git clone <repo-url>
cd <name>
/env-check        # set up the programming environment
```

## Branching model

- `main` — stable, release-ready
- `feat/<name>` — new features
- `fix/<issue>-<slug>` — bug fixes

## Pull requests

- One logical change per PR
- Include tests for new behavior
- Update `CHANGELOG.md` under `[Unreleased]`
- PR title: imperative mood ("Add X", not "Added X")

## Code style

<!-- Link to style guide or describe conventions here -->
```

### CHANGELOG.md

```markdown
# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added

### Changed

### Fixed
```

### PULL_REQUEST_TEMPLATE.md

```markdown
## Summary

<!-- What does this PR do? -->

## Changes

-

## Test plan

- [ ] Existing tests pass
- [ ] New tests added for new behavior
- [ ] CHANGELOG.md updated under [Unreleased]
```

### .github/workflows/test.yml

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up environment
        run: # language-specific setup (e.g., pip install -e ".[dev]")
      - name: Run tests
        run: # test command (e.g., pytest / cargo test / go test ./...)
```

### .github/workflows/publish.yml

```yaml
name: Publish

on:
  push:
    tags: ['v*']

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and publish
        run: # language-specific publish step
```

---

## .gitignore additions

Beyond the standard language entries from `references/git.md`, add:

```
dist/
build/
*.egg-info/
.eggs/
```

---

## CLAUDE.md template

```markdown
## Project

**Type:** coding-tool
**Language:** <language>
**Description:** <description>

## Commands

| Task | Command |
|---|---|
| Install (dev) | `<install command>` |
| Run tests | `<test command>` |
| Lint | `<lint command>` |
| Format | `<format command>` |
| Build | `<build command>` |
| Publish | `<publish command>` |

## Code conventions

- Style guide: <PEP 8 / rustfmt / gofmt / StandardJS / project-specific>
- All public API must be documented
- Tests required for new behavior (target: >80% coverage)
- PR titles: imperative mood

## Repository layout

- `src/<name>/` — library source
- `tests/` — test suite (mirrors `src/` structure)
- `docs/` — documentation source
- `.github/workflows/` — CI/CD pipelines

## Contribution guidelines

See `CONTRIBUTING.md`. Branch from `main`; open a PR to merge back.
```

---

## Recommended Claude configuration

### LSP

**Critical** for this project type. Language server provides go-to-definition,
diagnostics on every edit, and find-references. Set up before writing significant code.

### Hooks

**High value.** PostToolUse Edit hooks run the linter and formatter after every file
Claude edits — enforces style automatically.

See `references/claude-config/hooks.md` for language-specific patterns.

### MCP

- **GitHub MCP**: PR review, issue tracking, release automation. Recommended if the
  project is hosted on GitHub.

### Recommended agents

**code-reviewer**

```yaml
name: code-reviewer
description: >
  Reviews staged changes or a specified file against the project's contribution
  guidelines and code conventions. Use when asked to "review my changes", "is this
  PR-ready?", or "check my code".
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
maxTurns: 10
```

Body: Load `CONTRIBUTING.md` and the `## Code conventions` section of `CLAUDE.md`.
Review the diff or specified files. Produce a structured review with blocking issues,
non-blocking suggestions, and explicit approval or request-for-changes verdict.

---

**test-writer**

```yaml
name: test-writer
description: >
  Generates test cases for a specified function, module, or feature. Use when asked
  to "write tests for X" or "add test coverage for Y".
tools: Read, Grep, Glob, Write, Edit
model: inherit
permissionMode: default
maxTurns: 15
```

Body: Read the target file. Identify untested or under-tested paths. Write test cases
in `tests/` mirroring the source structure. Follow project test conventions. Do not
modify source files.

---

**changelog-updater**

```yaml
name: changelog-updater
description: >
  Reads recent git changes and writes a CHANGELOG.md entry under [Unreleased]. Use
  when asked to "update the changelog" or "document these changes".
tools: Read, Bash, Edit
model: inherit
permissionMode: default
maxTurns: 5
```

Body: Run `git log --oneline <base>..HEAD`. Categorize commits into Added / Changed /
Fixed. Write entries under `## [Unreleased]` in `CHANGELOG.md`. Keep entries
user-facing and concise.

### Recommended local skills

None required — the agents above cover the primary workflows.
