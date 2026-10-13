#!/usr/bin/env bash
# collect.sh — list every instruction source config-reconcile must read for one project
#
# Usage: collect.sh [project-path]     (default: current directory)
#
# Prints four sections: project, reference set, project instruction files, auto-memory.
# Read-only. Exits 1 if the project path does not exist.

set -euo pipefail

proj="$(cd "${1:-.}" 2>/dev/null && pwd)" || { echo "Error: no such directory: ${1:-.}" >&2; exit 1; }
claude_home="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

echo "## Project"
echo "path: $proj"

top="$(git -C "$proj" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$top" ]]; then
  echo "git: none"
  echo "ownership: not-git (memory only unless the user says otherwise)"
else
  echo "git: $top"
  echo "branch: $(git -C "$top" branch --show-current)"
  echo "default-branch: $(git -C "$top" symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##' || echo unknown)"
  echo "dirty: $( [[ -n "$(git -C "$top" status --porcelain)" ]] && echo yes || echo no)"
  origin="$(git -C "$top" remote get-url origin 2>/dev/null || true)"
  upstream="$(git -C "$top" remote get-url upstream 2>/dev/null || true)"
  echo "origin: ${origin:-none}"
  echo "upstream: ${upstream:-none}"
  # Owner = path segment before the repo name, for both ssh and https URLs.
  owner="$(sed -E 's#^.*[:/]([^/]+)/[^/]+$#\1#' <<<"$origin")"
  me="$(git config --global github.user 2>/dev/null || echo bcmcpher)"
  if [[ -z "$origin" ]]; then
    ownership="local (no remote; treat as owned, confirm with the user)"
  elif [[ "$owner" != "$me" ]]; then
    ownership="upstream (origin owned by $owner; memory only)"
  elif [[ -n "$upstream" ]]; then
    ownership="fork (has an upstream remote; its CLAUDE.md is probably upstream's; confirm with the user)"
  else
    ownership="owned"
  fi
  echo "ownership: $ownership"
fi

echo
echo "## Reference set (global)"
global="$claude_home/CLAUDE.md"
echo "$global"
# Resolve @imports: a line that is only "@path".
grep -E '^@[^[:space:]]+$' "$global" 2>/dev/null | sed 's/^@//' | while read -r imp; do
  case "$imp" in
    /*) p="$imp" ;;
    "~/"*) p="$HOME/${imp#\~/}" ;;
    *) p="$(dirname "$global")/$imp" ;;
  esac
  [[ -f "$p" ]] && echo "$p" || echo "$p (MISSING)"
done

echo
echo "## Project instruction files"
refs=("$global")
while read -r imp; do
  case "$imp" in /*) refs+=("$imp") ;; "~/"*) refs+=("$HOME/${imp#\~/}") ;; *) refs+=("$(dirname "$global")/$imp") ;; esac
done < <(grep -E '^@[^[:space:]]+$' "$global" 2>/dev/null | sed 's/^@//')
root="${top:-$proj}"
find "$root" -maxdepth 4 \
  \( -name node_modules -o -name .venv -o -name venv -o -name .git -o -name .tox -o -name build -o -name dist -o -path "$root/.claude/worktrees" \) -prune -o \
  -type f \( -name CLAUDE.md -o -name CLAUDE.local.md -o -name AGENTS.md -o -path '*/.claude/rules/*.md' \) -print 2>/dev/null \
  | sort | while read -r f; do
      tracked=untracked
      [[ -n "$top" ]] && git -C "$top" ls-files --error-unmatch "$f" >/dev/null 2>&1 && tracked=tracked
      same=""
      for r in "${refs[@]}"; do cmp -s "$f" "$r" && same=", IDENTICAL to $r: skip"; done
      echo "$f ($tracked, $(wc -l <"$f") lines$same)"
    done

# Claude Code also loads CLAUDE.md from every ancestor directory of the working directory.
d="$(dirname "$root")"
while [[ "$d" != "/" && "$d" != "$HOME" && "$d" == "$HOME"/* ]]; do
  for n in CLAUDE.md CLAUDE.local.md; do
    [[ -f "$d/$n" ]] && echo "$d/$n (ancestor, outside the repo, $(wc -l <"$d/$n") lines)"
  done
  d="$(dirname "$d")"
done

echo
echo "## Auto-memory"
# Claude Code names the project dir after the absolute path with every non-alphanumeric char → '-'.
for p in "$proj" ${top:+"$top"}; do
  slug="$(sed 's/[^a-zA-Z0-9]/-/g' <<<"$p")"
  mem="$claude_home/projects/$slug/memory"
  [[ -d "$mem" ]] || continue
  echo "slug: $slug"
  echo "dir: $mem"
  index="$mem/MEMORY.md"
  find "$mem" -maxdepth 1 -type f -name '*.md' | sort | while read -r f; do
    b="$(basename "$f")"
    [[ "$b" == MEMORY.md ]] && continue
    if [[ -f "$index" ]] && grep -qF "($b)" "$index"; then echo "$f"; else echo "$f (NOT INDEXED)"; fi
  done
  if [[ -f "$index" ]]; then
    grep -oE '\([^)]+\.md\)' "$index" | tr -d '()' | sort -u | while read -r link; do
      [[ -f "$mem/$link" ]] || echo "DANGLING LINK in MEMORY.md: $link"
    done
  else
    echo "MEMORY.md missing"
  fi
  break
done
