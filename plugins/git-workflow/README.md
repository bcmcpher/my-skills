# git-workflow

Git workflow best practices and PR lifecycle commands for Claude Code sessions.

Provides decision context for choosing between in-place commits, branches, and
worktrees; commit conventions; parallel-agent coordination; conflict resolution;
and slash commands for the full commit → push → PR lifecycle.

## Install

```bash
# Session-only (for testing)
claude --plugin-dir ./plugins/git-workflow

# Permanent install
claude plugin install ./plugins/git-workflow
```

## Commands

| Command | What it does |
|---|---|
| `/commit` | Stage and commit changes with a conventional message |
| `/commit-push-pr` | Commit, push to origin, and open a GitHub PR |
| `/review-pr [number]` | Review an open PR and post findings as a comment |
| `/clean-gone` | Remove local branches/worktrees deleted on the remote |

## Skill

`/git-workflow` — Auto-invoked decision guide for git strategy, commit cadence,
parallel agent coordination, and conflict resolution.
