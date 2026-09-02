#!/bin/bash
# graph-update.sh — gate for the code-review-graph hooks.
#
# Usage: graph-update.sh status | update | full-update
#
# The three code-review-graph hooks are wired globally, so the wiring lives in
# one place and travels with this config. But global wiring fails OPEN: without
# a gate, every repository ever edited gets a graph built in it, including
# clones of other people's projects and repos that track no code at all.
#
# The gate is the graph's own directory. A repo participates if and only if
# <repo>/.code-review-graph/ already exists, which means:
#
#   opt in:  cd <repo> && code-review-graph build
#   opt out: rm -rf <repo>/.code-review-graph   (or code-review-graph uninstall)
#
# No list to maintain, nothing committed to any repo, and nothing happens in a
# repo until it is asked for. `.code-review-graph/` ships its own .gitignore
# covering itself, so opting in adds no files to the repo's index either.
#
# Upstream's alternative is `code-review-graph install` per repo, which writes
# .claude/settings.json, .mcp.json, CLAUDE.md instructions and a git pre-commit
# hook into the worktree — all committed, and all pointing at
# ~/.claude-lsp-tools paths that only exist on this machine.

CRG="$HOME/.claude-lsp-tools/bin/code-review-graph"
ACTION="${1:-status}"

[ -x "$CRG" ] || exit 0

# Not a git repository: the parent directory holding several repos, a scratch
# dir, $HOME. code-review-graph exits non-zero here, which is why the bare hook
# commands needed `|| true`. Gating removes the need for that.
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$REPO_ROOT" ] || exit 0

[ -d "$REPO_ROOT/.code-review-graph" ] || exit 0

case "$ACTION" in
    status)      "$CRG" status ;;
    update)      "$CRG" update --skip-flows -q ;;
    full-update) "$CRG" update -q ;;
    *) echo "graph-update.sh: unknown action '$ACTION'" >&2; exit 0 ;;
esac

# Never fail the hook. A graph that is mid-migration or briefly locked is not a
# reason to surface an error to the model on every edit.
exit 0
