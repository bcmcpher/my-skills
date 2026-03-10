#!/bin/bash
# git-guard.sh — PreToolUse hook for Bash commands
# Blocks bare `mv` on git-tracked files and direct .git/ manipulation.

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# Case B: direct .git/ manipulation
if echo "$COMMAND" | grep -qE '(^|[[:space:]/])\.git(/|$)'; then
  echo "Blocked: command targets .git/ directory" >&2
  exit 2
fi

# Case A: bare mv on a tracked file
if [[ "$COMMAND" == mv\ * ]]; then
  # Extract the source (first non-option argument after mv)
  SRC=$(echo "$COMMAND" | sed 's/^mv[[:space:]]*//' | awk '{print $1}')
  if [[ -n "$SRC" ]] && git ls-files --error-unmatch "$SRC" 2>/dev/null; then
    echo "$SRC is tracked by git. Use: git mv $SRC <dst>" >&2
    exit 2
  fi
fi

exit 0
