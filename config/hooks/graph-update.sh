#!/bin/bash
# graph-update.sh — gate for the code-graph hooks (code-review-graph, CodeGraph).
#
# Usage: graph-update.sh status | update | full-update
#
# The three code-review-graph hooks are wired globally, so the wiring lives in
# one place and travels with this config. But global wiring fails OPEN: without
# a gate, every repository ever edited gets a graph built in it, including
# clones of other people's projects and repos that track no code at all.
#
# The gate is the graph's own directory. A repo participates in a tool if and
# only if that tool's index directory already exists — .code-review-graph/ or
# .codegraph/ — which for code-review-graph means:
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
CG="$HOME/.claude-node-tools/bin/codegraph"
ACTION="${1:-status}"

# Not a git repository: the parent directory holding several repos, a scratch
# dir, $HOME. code-review-graph exits non-zero here, which is why the bare hook
# commands needed `|| true`. Gating removes the need for that.
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
[ -n "$REPO_ROOT" ] || exit 0

# code-review-graph: opted in by <repo>/.code-review-graph/
if [ -x "$CRG" ] && [ -d "$REPO_ROOT/.code-review-graph" ]; then
    case "$ACTION" in
        status)      "$CRG" status ;;
        update)      "$CRG" update --skip-flows -q ;;
        full-update) "$CRG" update -q ;;
        *) echo "graph-update.sh: unknown action '$ACTION'" >&2 ;;
    esac
fi

# CodeGraph: opted in by <repo>/.codegraph/ (cd <repo> && codegraph init --yes).
# CODEGRAPH_NO_DAEMON keeps it from starting a background watcher; these hooks
# do the incremental sync instead. Telemetry is off via settings.json env.
if [ -x "$CG" ] && [ -d "$REPO_ROOT/.codegraph" ]; then
    export CODEGRAPH_NO_DAEMON=1
    case "$ACTION" in
        # Full status is ~30 lines and lands in context every session; keep the counts.
        status)      "$CG" status "$REPO_ROOT" 2>/dev/null \
                       | grep -E '^\s*(Files|Nodes|Edges):|up to date|stale|pending' \
                       | sed 's/^\s*/CodeGraph /' ;;
        update)      "$CG" sync "$REPO_ROOT" >/dev/null 2>&1 ;;
        full-update) "$CG" sync "$REPO_ROOT" >/dev/null 2>&1 ;;
    esac
fi

# Never fail the hook. A graph that is mid-migration or briefly locked is not a
# reason to surface an error to the model on every edit.
exit 0
