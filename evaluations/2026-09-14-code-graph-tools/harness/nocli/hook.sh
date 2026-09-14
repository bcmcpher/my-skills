#!/usr/bin/env bash
# PreToolUse(Bash): deny codegraph / code-review-graph at command position, however they are
# spelled (bare, absolute path, after env assignments, in a pipeline or substitution).
# Pattern follows codegraph's own scripts/agent-eval/no-cli-shim.sh, extended to CRG.
cmd=$(jq -r '.tool_input.command // empty')
re='(^|[;&|(]|&&|\|\||\$\(|`)[[:space:]]*([A-Za-z_][A-Za-z0-9_]*=[^[:space:]]*[[:space:]]+)*[A-Za-z0-9_./~-]*(codegraph|code-review-graph)([[:space:]]|$)'
if [[ "$cmd" =~ $re ]]; then
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"graph tool CLIs are blocked in this benchmark"}}\n'
fi
exit 0
