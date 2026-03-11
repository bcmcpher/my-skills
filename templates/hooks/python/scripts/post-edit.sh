#!/bin/bash
# post-edit.sh — PostToolUse hook for Python files
#
# Runs linting and formatting tools after Claude writes or edits a file.
# Auto-fix tools are applied in-place. Type checkers warn but don't block.
# Non-.py files are silently ignored (exit 0).
#
# Set the ENABLE_* variables below to 1 to activate each tool.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Bail silently if not a Python file
[[ "$FILE_PATH" == *.py ]] || exit 0

# Bail silently if file does not exist
[[ -f "$FILE_PATH" ]] || exit 0

# ── Configuration ────────────────────────────────────────────────────────────
ENABLE_RUFF=0
ENABLE_BLACK=0
ENABLE_FLAKE8=0
ENABLE_MYPY=0
# ─────────────────────────────────────────────────────────────────────────────

WARNINGS=0
FORMATTED=0

# --- ruff (linting + formatting) ---
if [[ "$ENABLE_RUFF" == "1" ]]; then
  if command -v ruff &>/dev/null; then
    echo "[post-edit] ruff check --fix: $FILE_PATH"
    ruff check --fix "$FILE_PATH"
    echo "[post-edit] ruff format: $FILE_PATH"
    ruff format "$FILE_PATH"
    FORMATTED=1
  else
    echo "[post-edit] ruff not found — skipping (install: pip install ruff)" >&2
  fi
fi

# --- black (formatting) ---
# Skipped if ruff already formatted the file.
if [[ "$ENABLE_BLACK" == "1" && "$FORMATTED" == "0" ]]; then
  if command -v black &>/dev/null; then
    echo "[post-edit] black: $FILE_PATH"
    black "$FILE_PATH"
    FORMATTED=1
  else
    echo "[post-edit] black not found — skipping (install: pip install black)" >&2
  fi
fi

# --- flake8 (linting, check-only) ---
if [[ "$ENABLE_FLAKE8" == "1" ]]; then
  if command -v flake8 &>/dev/null; then
    echo "[post-edit] flake8: $FILE_PATH"
    flake8 "$FILE_PATH" || WARNINGS=1
  else
    echo "[post-edit] flake8 not found — skipping (install: pip install flake8)" >&2
  fi
fi

# --- mypy (type checking, check-only) ---
if [[ "$ENABLE_MYPY" == "1" ]]; then
  if command -v mypy &>/dev/null; then
    echo "[post-edit] mypy: $FILE_PATH"
    mypy "$FILE_PATH" || WARNINGS=1
  else
    echo "[post-edit] mypy not found — skipping (install: pip install mypy)" >&2
  fi
fi

# Exit 1 (warn) if check-only tools found issues — does not block, Claude sees the output
# Exit 0 if everything passed or only auto-fix tools ran
exit $WARNINGS
