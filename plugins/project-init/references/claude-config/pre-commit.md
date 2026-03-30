# Pre-commit hooks reference

Pre-commit hooks run before each `git commit` and are independent of Claude Code
PostToolUse hooks. Use both together: Claude Code hooks enforce quality during AI-assisted
editing sessions; pre-commit hooks enforce quality at commit time regardless of how the
code was changed.

The `.pre-commit-config.yaml` stubs below mirror the tools used in `hooks.md` so both
systems stay aligned.

---

## Setup

```bash
pip install pre-commit   # or: brew install pre-commit / conda install pre-commit
pre-commit install       # installs the git hook into .git/hooks/pre-commit
```

After installation, hooks run automatically on `git commit`. To run manually:

```bash
pre-commit run --all-files   # check everything
pre-commit run <hook-id>     # check one hook
```

---

## Language stubs

### Python (ruff)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Requires `ruff` installed in the environment (or pre-commit will manage it automatically
via the repo hook). Compatible with the ruff PostToolUse Claude Code hook.

---

### JavaScript / TypeScript (eslint + prettier)

```yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.3.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        types: [file]
        additional_dependencies:
          - eslint@^9
          # add project-specific eslint plugins here
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.3.0
    hooks:
      - id: prettier
        files: \.[jt]sx?$
```

---

### Rust (rustfmt + clippy)

```yaml
repos:
  - repo: local
    hooks:
      - id: rustfmt
        name: rustfmt
        language: system
        entry: cargo fmt --
        types: [rust]
        pass_filenames: false
      - id: clippy
        name: clippy
        language: system
        entry: cargo clippy -- -D warnings
        types: [rust]
        pass_filenames: false
```

Note: `language: system` requires the Rust toolchain to be installed. These hooks will
fail if `cargo` is not on PATH.

---

### Go (gofmt + go vet)

```yaml
repos:
  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-vet
      - id: go-unit-tests
```

---

### R (styler + lintr)

```yaml
repos:
  - repo: https://github.com/lorenzwalthert/precommit
    rev: v0.4.3
    hooks:
      - id: style-files
        args: [--style_pkg=styler, --style_fun=tidyverse_style]
      - id: lintr
```

Requires `precommit` R package: `install.packages("precommit")`.

---

## Universal additions (all projects)

Add these to any config to catch common cross-language issues:

```yaml
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-merge-conflict
      - id: detect-private-key
```

`detect-private-key` is particularly valuable — it blocks accidental commits of
private keys and API tokens.

---

## Relationship to Claude Code hooks

| System | When it runs | Configured in |
|---|---|---|
| Claude Code PostToolUse hooks | During Claude editing sessions | `.claude/hooks.json` |
| pre-commit hooks | On every `git commit` | `.pre-commit-config.yaml` |

Configuring one does not configure the other. Both are recommended for coding-tool
projects. For data-analysis and info-management projects, pre-commit is optional.
