---
allowed-tools: Bash(git branch:*), Bash(git worktree:*)
description: Remove local branches (and their worktrees) that have been deleted on the remote
---

## Your task

Clean up local branches marked as `[gone]` — branches whose remote tracking ref has been deleted (typically after a PR merges).

1. List all branches to identify `[gone]` entries:
   ```bash
   git branch -v
   ```
   Branches prefixed with `+` have associated worktrees and must have their worktree removed before deletion.

2. List worktrees to identify which ones need removal:
   ```bash
   git worktree list
   ```

3. For each `[gone]` branch, remove its worktree (if any) then delete the branch:
   ```bash
   git branch -v | grep '\[gone\]' | sed 's/^[+* ]//' | awk '{print $1}' | while read branch; do
     echo "Processing branch: $branch"
     worktree=$(git worktree list | grep "\\[$branch\\]" | awk '{print $1}')
     if [ ! -z "$worktree" ] && [ "$worktree" != "$(git rev-parse --show-toplevel)" ]; then
       echo "  Removing worktree: $worktree"
       git worktree remove --force "$worktree"
     fi
     if git branch -d "$branch" 2>/dev/null; then
       echo "  Deleted branch: $branch"
     else
       echo "  SKIPPED (unmerged): $branch — run 'git branch -D $branch' to force-delete"
     fi
   done
   ```

If no branches are marked `[gone]`, report that no cleanup was needed.
