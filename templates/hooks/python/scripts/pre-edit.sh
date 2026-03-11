#!/bin/bash
# pre-edit.sh — PreToolUse hook for Python files
#
# Runs linting tools in check-only mode before Claude edits a file.
# Reports issues as warnings (exit 1) so Claude can see the baseline.
# Non-.py files are silently ignored (exit 0).
#
# Set the ENABLE_* variables below to 1 to activate each tool.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Bail silently if not a Python file
[[ "$FILE_PATH" == *.py ]] || exit 0

# Bail silently if file does not exist (new file being created)
[[ -f "$FILE_PATH" ]] || exit 0

# ── Configuration ────────────────────────────────────────────────────────────
ENABLE_RUFF=0
ENABLE_FLAKE8=0
ENABLE_MYPY=0
# ─────────────────────────────────────────────────────────────────────────────

ISSUES=0

# --- ruff (linting) ---
if [[ "$ENABLE_RUFF" == "1" ]]; then
  if command -v ruff &>/dev/null; then
    echo "[pre-edit] ruff check: $FILE_PATH"
    ruff check "$FILE_PATH" || ISSUES=1
  else
    echo "[pre-edit] ruff not found — skipping (install: pip install ruff)" >&2
  fi
fi

# --- flake8 (linting) ---
if [[ "$ENABLE_FLAKE8" == "1" ]]; then
  if command -v flake8 &>/dev/null; then
    echo "[pre-edit] flake8: $FILE_PATH"
    flake8 "$FILE_PATH" || ISSUES=1
  else
    echo "[pre-edit] flake8 not found — skipping (install: pip install flake8)" >&2
  fi
fi

# --- mypy (type checking) ---
if [[ "$ENABLE_MYPY" == "1" ]]; then
  if command -v mypy &>/dev/null; then
    echo "[pre-edit] mypy: $FILE_PATH"
    mypy "$FILE_PATH" || ISSUES=1
  else
    echo "[pre-edit] mypy not found — skipping (install: pip install mypy)" >&2
  fi
fi

# Exit 1 (warn) if any tool found issues — Claude sees the output but the edit proceeds
exit $ISSUES
