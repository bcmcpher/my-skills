#!/usr/bin/env bash
# check-droplog.sh — verify that a drop log records everything the reconcile pass removed
#
# Usage: check-droplog.sh <drop-log> [--repo <git-dir> <base-ref>] [--memory <backup-dir> <live-dir>]
#
#   --repo    every non-blank line removed in `git diff <base-ref>` (committed and working tree)
#             must appear verbatim in the drop log.
#   --memory  every memory file in the backup but not in the live dir must be named in the drop
#             log, and every non-blank line of its body must appear verbatim.
#
# Prints each missing item. Exits 1 if anything is missing, 0 if the log is complete.

set -euo pipefail

usage() { sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }
[[ $# -ge 1 ]] || usage
log="$1"; shift
[[ -f "$log" ]] || { echo "Error: drop log not found: $log" >&2; exit 2; }

missing=0
in_log() { grep -qF -- "$1" "$log"; }
report() { echo "MISSING: $1"; missing=$((missing + 1)); }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      repo="$2"; base="$3"; shift 3
      # Removed lines from files other than the drop log itself; strip the leading '-' and edge whitespace.
      while IFS= read -r line; do
        text="$(sed -E 's/^-//; s/^[[:space:]]+//; s/[[:space:]]+$//' <<<"$line")"
        [[ -z "$text" ]] && continue
        in_log "$text" || report "diff line: $text"
      done < <(git -C "$repo" diff "$base" -- . ":(exclude).claude/reconcile-*.md" \
                 | grep -E '^-' | grep -vE '^--- ')
      ;;
    --memory)
      backup="$2"; live="$3"; shift 3
      for f in "$backup"/*.md; do
        b="$(basename "$f")"
        [[ -f "$live/$b" ]] && continue
        in_log "$b" || report "memory file not named: $b"
        while IFS= read -r line; do
          text="$(sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//' <<<"$line")"
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
