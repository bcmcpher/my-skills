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

## Stash (save work in progress without committing)

Use `git stash` when you need to switch context mid-work and aren't ready to commit.

```bash
# Save all tracked modifications (staged and unstaged)
git stash push -m "description of WIP"

# Include untracked files too
git stash push -u -m "description of WIP"

# List saved stashes
git stash list

# Restore the most recent stash (keeps it in the list)
git stash apply

# Restore and remove from the list
git stash pop

# Restore a specific stash
git stash apply stash@{2}

# Discard a stash you no longer need
git stash drop stash@{0}

# Clear all stashes
git stash clear
```

**When to stash vs. commit WIP:**

| Situation | Prefer |
|---|---|
| Switching to a hotfix on the same repo | `git stash push -u` |
| Work is coherent enough to checkpoint | WIP commit (`git commit -m "wip: ..."`) |
| Pulling remote updates mid-work | `git stash push` → `git pull` → `git stash pop` |
| Switching branches (clean working tree required) | `git stash push` |

WIP commits are generally preferable to stashes for anything that will take more than a few minutes — stashes are easy to forget and don't appear in `git log`.

## Fetch before starting parallel work

Always fetch to ensure branches start from the latest remote state:

```bash
git fetch origin
git checkout -b feature/my-task origin/main
```
