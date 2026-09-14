#!/usr/bin/env bash
# run.sh <arm: base|crg|cg> <question: Q1..Q4> <rep> — one headless benchmark run on the crane clone.
#   base: no MCP servers.  crg / cg: that tool's MCP server + its installer CLAUDE.md guidance.
#   BASH=1 allows Bash in every arm (the original harness does), with both graph CLIs blocked by a
#   PreToolUse hook; BASH=0 (default) disallows Bash entirely.
#   All arms: subscription auth, no user settings/hooks/plugins, tool search off, dontAsk.
set -euo pipefail
arm="$1"; q="$2"; rep="${3:-1}"; E=/tmp/codegraph-eval; V=$E/v3
case "$arm" in
  base) mcp=$V/mcp-none.json; graph=""; guide="" ;;
  crg)  mcp=$V/mcp-crg.json;  graph="mcp__crg__*"; guide=$V/guide-crg.md ;;
  cg)   mcp=$V/mcp-cg.json;   graph="mcp__codegraph__*"; guide=$V/guide-cg.md ;;
  *) echo "arm must be base|crg|cg" >&2; exit 2 ;;
esac
name="$q.$arm.r$rep"; out=$V/runs/$name
allow=(Read Grep Glob); deny=(Edit Write NotebookEdit WebFetch WebSearch Agent)
[[ -n "$graph" ]] && allow+=("$graph")
extra=()
if [[ "${BASH:-0}" == 1 ]]; then allow+=(Bash); extra+=(--settings "$V/nocli/settings.json"); else deny+=(Bash); fi
[[ -n "$guide" ]] && extra+=(--append-system-prompt "$(cat "$guide")")
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
cd "$E/crane"
qdir="$V/questions"; [[ "${VARIANT:-a}" == b ]] && qdir="$V/questions-b"
prompt="$(cat "$qdir/$q.txt")"
# VARIANT=b: graph arms get one sentence pointing at their tool, in the user prompt itself.
if [[ "${VARIANT:-a}" == b && "$arm" == crg ]]; then
  prompt="$prompt"$'\n\n'"This repository is indexed by code-review-graph. Use its MCP tools (mcp__crg__*) as your primary source; target symbols as path::Symbol, e.g. src/crane/utils/coords.py::world_to_voxel_indices. Read files only to confirm details."
elif [[ "${VARIANT:-a}" == b && "$arm" == cg ]]; then
  prompt="$prompt"$'\n\n'"This repository is indexed by CodeGraph. Use its MCP tool (codegraph_explore) as your primary source. Read files only to confirm details."
fi
name="$name.${VARIANT:-a}"; out=$V/runs/$name
date -u +%Y-%m-%dT%H:%M:%SZ > "$out.start"
ENABLE_TOOL_SEARCH=false claude -p "$prompt" \
  --model opus --output-format stream-json --verbose \
  --setting-sources project --strict-mcp-config --mcp-config "$mcp" \
  --permission-mode dontAsk --allowedTools "${allow[@]}" --disallowedTools "${deny[@]}" \
  --max-budget-usd 4 "${extra[@]}" \
  < /dev/null > "$out.stream.jsonl" 2> "$out.stderr" || echo "exit=$?" >> "$out.stderr"
date -u +%Y-%m-%dT%H:%M:%SZ > "$out.end"
echo "$name done"
