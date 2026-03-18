# Worktree Patterns

Reference for common worktree command sequences in Claude Code agentic workflows.

## Lifecycle: agent with isolation: worktree

When an agent's SKILL.md frontmatter includes `isolation: worktree`, Claude Code
automatically creates a temporary git worktree before the agent runs and cleans it
up after:

- If agent makes no changes → worktree is removed, no branch left behind
- If agent makes changes → branch and worktree path are returned to the caller

You don't need to manage this manually — set `isolation: worktree` and the harness
handles it.

## Manual worktree management (when not using isolation: worktree)

```bash
# List all active worktrees
git worktree list

# Create a worktree for parallel work on a new branch
git worktree add ../my-repo-feature-x -b feature/my-feature-x

# Create from an existing branch
git worktree add ../my-repo-fix-y fix/existing-branch

# Remove when done (branch is NOT deleted — remove separately if needed)
git worktree remove ../my-repo-feature-x

# Prune stale worktree references (e.g. after deleting the directory manually)
git worktree prune
```

## Merging parallel worktree branches

After parallel agents finish, merge in dependency order:

```bash
# 1. Identify common ancestor
git merge-base feature/agent-a feature/agent-b

# 2. Merge leaf branch first (no dependencies)
git checkout main
git rebase feature/agent-a   # or git merge --no-ff feature/agent-a

# 3. Rebase dependent branch onto updated main
git checkout feature/agent-b
git rebase main
git checkout main
git rebase feature/agent-b

# 4. Clean up branches
git branch -d feature/agent-a feature/agent-b
```

## Fetch before starting parallel work

Always fetch to ensure branches start from the latest remote state:

```bash
git fetch origin
git checkout -b feature/my-task origin/main
```
