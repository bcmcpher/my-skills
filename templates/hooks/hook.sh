#!/bin/bash
# HOOK_NAME.sh — PreToolUse / PostToolUse hook
#
# Wire into config/settings.json under the appropriate event:
#
#   "hooks": {
#     "PreToolUse": [
#       {
#         "matcher": "Bash|Edit|Write",
#         "hooks": [{ "type": "command", "command": "~/.claude/hooks/HOOK_NAME.sh" }]
#       }
#     ]
#   }
#
# Then run: bin/sync-config push
#
# Exit codes:
#   0  — allow the tool call to proceed
#   1  — warn (show output to Claude, but continue)
#   2  — block (abort the tool call, show output as error)

# shellcheck disable=SC2034  # COMMAND and FILE_PATH are stubs for user logic below
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Add your logic here.
# Examples:
#   Block a command:      echo "Blocked: reason" >&2; exit 2
#   Warn about a file:    echo "Warning: ..." >&2; exit 1
#   Check a file path:    if [[ "$FILE_PATH" == *.env ]]; then ...

exit 0
