#!/usr/bin/env bash
# check-droplog.sh — verify that a drop log records everything the reconcile pass removed
#
# Usage: check-droplog.sh <drop-log> [--repo <git-dir> <base-ref>] [--memory <backup-dir> <live-dir>]
#
#   --repo    every non-blank line removed since the merge-base of <base-ref> and HEAD (committed
#             and working tree) must appear verbatim inside a fenced block of the drop log.
#   --memory  every memory file in the backup but not in the live dir must be named in the drop
#             log; every non-blank line of its body, and every line removed from a memory file
#             that was kept and edited (MEMORY.md included), must appear inside a fenced block.
#
# Prints each missing item. Exits 1 if anything is missing, 0 if the log is complete.

set -euo pipefail

usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
[[ $# -ge 1 ]] || usage
log="$1"; shift
[[ -f "$log" ]] || { echo "Error: drop log not found: $log" >&2; exit 2; }

# Only text inside ``` or ~~~ fences counts as logged, so a removed line cannot pass by matching
# the quoted global rule or the prose around it.
fenced="$(mktemp)"; trap 'rm -f "$fenced"' EXIT
# A fence closes only on a bare run of its own character at least as long as the opener, so a
# ```` block can quote text that contains ``` fences.
awk '
  !fence && match($0, /^[[:space:]]*(```+|~~~+)/) {
    fence = substr($0, RSTART, RLENGTH); sub(/^[[:space:]]+/, "", fence); next
  }
  fence {
    line = $0; gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
    rest = line; gsub(substr(fence, 1, 1) == "`" ? "`" : "~", "", rest)
    if (rest == "" && length(line) >= length(fence)) { fence = ""; next }
    print
  }' "$log" >"$fenced"

missing=0
in_log() { grep -qF -- "$1" "$fenced"; }
report() { echo "MISSING: $1"; missing=$((missing + 1)); }
trim() { sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' <<<"$1"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="$2"; base="$(git -C "$2" merge-base "$3" HEAD)"; shift 3
      # Removed lines from files other than the drop log itself. Header lines end at each '@@'.
      while IFS= read -r line; do
        text="$(trim "$line")"
        [[ -z "$text" ]] && continue
        in_log "$text" || report "diff line: $text"
      done < <(git -C "$repo" diff --no-color --no-ext-diff "$base" -- . ":(exclude).claude/reconcile-*.md" \
                 | awk '/^diff --git / { hunk = 0; next } /^@@/ { hunk = 1; next } hunk && /^-/ { print substr($0, 2) }')
      ;;
    --memory)
      backup="$2"; live="$3"; shift 3
      for f in "$backup"/*.md; do
        [[ -f "$f" ]] || { echo "Error: no memory files in $backup" >&2; exit 2; }
        b="$(basename "$f")"
        if [[ -f "$live/$b" ]]; then
          # Kept file: check the lines the edit removed.
          while IFS= read -r line; do
            text="$(trim "$line")"
            [[ -z "$text" || "$text" == "---" ]] && continue
            in_log "$text" || report "$b removed line: $text"
          done < <(diff "$f" "$live/$b" | sed -n 's/^< //p' || true)
          continue
        fi
        grep -qF -- "$b" "$log" || report "memory file not named: $b"
        while IFS= read -r line || [[ -n "$line" ]]; do
          text="$(trim "$line")"
          [[ -z "$text" || "$text" == "---" ]] && continue
          in_log "$text" || report "$b body line: $text"
        done <"$f"
      done
      ;;
    *) usage ;;
  esac
done

if [[ $missing -eq 0 ]]; then
  echo "drop log complete"
else
  echo "$missing item(s) missing from $log"
  exit 1
fi
