# Python Environment Reference

## Environment indicator

`.venv/` directory in the project root.

---

## Tool priority

Check for `uv` first — it is significantly faster than pip for most workflows:

```bash
which uv
```

- `uv` found → use uv workflow below
- `uv` not found → use venv + pip workflow below

---

## uv workflow (preferred)

```bash
# Create virtual environment
uv venv .venv

# Install from pyproject.toml (with optional groups)
uv pip install -e ".[dev]"

# Install from requirements file
uv pip install -r requirements.txt

# Install from Pipfile (convert first)
uv pip install -r <(pipenv requirements)
```

---

## venv + pip workflow (fallback)

```bash
# Create virtual environment
python -m venv .venv

# Activate (needed for subsequent pip commands in this session)
source .venv/bin/activate

# Install from pyproject.toml
pip install -e ".[dev]"

# Install from requirements file
pip install -r requirements.txt

# Install from Pipfile
pip install pipenv && pipenv install --dev
```

---

## Which install command to use

| File present | Command |
|---|---|
| `pyproject.toml` with `[project]` table | `pip install -e ".[dev]"` or `uv pip install -e ".[dev]"` |
| `requirements.txt` | `pip install -r requirements.txt` |
| `requirements-dev.txt` or `requirements/dev.txt` | Install both base and dev files |
| `Pipfile` | `pipenv install --dev` (or convert to requirements first with uv) |
| None of the above | `pip install -e .` if `setup.py` present, otherwise ask |

---

## Verify

```bash
which python
```

The path must resolve inside `.venv/` — for example:
`.venv/bin/python` or `/home/user/project/.venv/bin/python`.

If it resolves to `/usr/bin/python` or `/usr/local/bin/python`, the environment is not
active and verification has failed.

---

## pyrightconfig.json note

After creating the environment, check if `pyrightconfig.json` exists. If not, offer to
create one pointing to the new environment:

```json
{
  "venvPath": ".",
  "venv": ".venv"
}
```

This enables Pyright LSP to resolve imports correctly within the project.

---

## Activate command (for CLAUDE.md)

```
source .venv/bin/activate
```

---

## Recommended hooks

PostToolUse Edit hooks to run after Claude edits a Python file:

```
ruff check --fix $FILE
```

```
ruff format $FILE
```

---

## Conda environments

Conda cannot be activated from within a running Claude Code session — `conda activate`
modifies shell state that subprocesses cannot inherit. When conda is detected, document
the environment in CLAUDE.md rather than attempting to create or activate it inline.

**CLAUDE.md entry for conda environments:**

```markdown
## Active Environment

- Language: Python (conda)
- Environment: <conda env name>
- Activate: conda activate <env-name>
- Note: activate manually before launching Claude Code
- Last setup: <YYYY-MM-DD>
```

If `environment.yml` exists, extract the env name and Python version from it:

```yaml
# Relevant fields in environment.yml
name: <env-name>
dependencies:
  - python=<version>
```

Tell the user: "Run `conda activate <env-name>` before launching Claude Code.
Once activated, Claude Code will pick up the correct interpreter automatically."

---

## Beyond this skill

- **Linter/formatter config** — the hooks above run with tool defaults. For
  project-specific rules, consult the tool's documentation (`ruff.toml`,
  `pyproject.toml [tool.ruff]`, etc.).
- **Test runner** — this skill sets up the runtime environment only. Test framework
  setup and configuration (pytest, unittest, etc.) is a separate step outside the
  scope of `/env-check`.
