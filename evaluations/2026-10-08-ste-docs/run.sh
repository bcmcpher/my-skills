#!/usr/bin/env bash
# A/B: does writing.md move the STE score of a README Claude writes?
# Arm "base": no style guidance. Arm "ste": config/writing.md appended to the system prompt.
# Run BEFORE writing.md is live in ~/.claude/, or both arms carry it.
#
#   evaluations/2026-10-08-ste-docs/run.sh [N] [plugin]    # defaults: 3 boutiques
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
n="${1:-3}"
plugin="${2:-boutiques}"
out="$here/runs/$(date +%Y%m%d-%H%M%S)"

if grep -q '@writing.md' "$HOME/.claude/CLAUDE.md" 2>/dev/null; then
  echo "writing.md is already imported by ~/.claude/CLAUDE.md; the base arm would carry it." >&2
  exit 1
fi

mkdir -p "$out"
prompt="Read plugins/$plugin/ and write a README.md for it: what it does, how to install it, \
how to use each skill or command. Print only the Markdown, with no preamble."
style="$(cat "$repo/config/writing.md")"

for i in $(seq 1 "$n"); do
  for arm in base ste; do
    args=(-p "$prompt" --model opus --permission-mode default --allowedTools "Read,Grep,Glob")
    [[ $arm == ste ]] && args+=(--append-system-prompt "$style")
    (cd "$repo" && claude "${args[@]}") > "$out/$arm-$i.md"
    echo "done $arm-$i"
  done
done

python3 -I "$here/ste_check.py" "$out"/base-*.md "$out"/ste-*.md | tee "$out/scores.txt"
