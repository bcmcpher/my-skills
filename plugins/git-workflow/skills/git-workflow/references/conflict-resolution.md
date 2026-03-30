# Conflict Resolution

Step-by-step decision logic for resolving merge/rebase conflicts in Claude Code sessions.

## Decision: rebase vs. merge vs. cherry-pick

| Situation | Strategy |
|-----------|----------|
| Feature branch behind main, linear history desired | `git rebase main` |
| Merging a completed feature PR (preserve branch point) | `git merge --no-ff` |
| Pulling a single commit from another branch | `git cherry-pick <sha>` |
| History already public (pushed); rebasing would rewrite it | `git merge` (never rebase public history) |
| Commit already pushed or merged; need to undo safely | `git revert <sha>` |

## Rebase workflow

```bash
# Start from the feature branch
git fetch origin
git rebase origin/main

# If conflicts arise during rebase:
# 1. Inspect conflicting files
git diff --name-only --diff-filter=U

# 2. Resolve each file (edit to remove markers), then:
git add <resolved-file>
git rebase --continue

# 3. To abort and return to original state:
git rebase --abort
```

## Interactive rebase (clean up before pushing)

Use `git rebase -i` to squash, reorder, reword, or drop commits before pushing.
Only use on commits that have not yet been pushed to a shared branch.

```bash
# Interactively rebase the last N commits
git rebase -i HEAD~N

# Rebase everything since branching from main
git rebase -i $(git merge-base HEAD main)
```

The editor opens a list of commits. Change the verb on each line:

| Verb | Effect |
|---|---|
| `pick` | Keep the commit as-is |
| `reword` | Keep commit, edit its message |
| `squash` | Merge into the previous commit, combine messages |
| `fixup` | Merge into the previous commit, discard this message |
| `drop` | Remove the commit entirely |

Save and close. Git replays the commits in order. If conflicts arise, resolve
them, run `git add <resolved>`, then `git rebase --continue`. To abort: `git rebase --abort`.

**Common pattern — squash a fixup into its parent:**
```bash
git commit --fixup <parent-sha>   # creates a "fixup! ..." commit
git rebase -i --autosquash HEAD~N # automatically moves fixup into position
```

## Merge conflict resolution

```bash
# After git merge produces conflicts:
# 1. List unmerged files
git diff --name-only --diff-filter=U

# 2. For each file, choose a resolution strategy:
git checkout --ours   <file>   # keep current branch version
git checkout --theirs <file>   # take incoming version entirely
# OR edit the file manually to combine both sides

# 3. Stage resolved files
git add <resolved-file>

# 4. Complete the merge
git commit   # uses auto-generated merge commit message
```

## Reading conflict markers

```
<<<<<<< HEAD
  (your current branch version)
=======
  (incoming / theirs version)
>>>>>>> feature/other-branch
```

- Everything between `<<<<<<< HEAD` and `=======` is the current branch
- Everything between `=======` and `>>>>>>>` is the incoming change
- Delete the markers and leave only the correct final content

## Cherry-pick

```bash
# Apply a single commit from another branch
git cherry-pick <sha>

# Apply a range (exclusive start, inclusive end)
git cherry-pick <start-sha>..<end-sha>

# If conflict: resolve, then
git add <resolved-file>
git cherry-pick --continue

# Abort:
git cherry-pick --abort
```

## Revert (undo a public commit)

Use `git revert` when the commit to undo has already been pushed or merged — it
creates a new commit that inverts the changes rather than rewriting history.

```bash
# Revert a single commit (opens editor for commit message)
git revert <sha>

# Revert without opening the editor
git revert --no-edit <sha>

# Revert a merge commit (specify which parent to keep, usually 1)
git revert -m 1 <merge-sha>

# Revert a range of commits (oldest first)
git revert <oldest-sha>..<newest-sha>
```

If the revert produces conflicts, resolve them the same way as a merge conflict
(edit files, `git add <resolved>`, `git revert --continue`). To abort: `git revert --abort`.

## Checking divergence before acting

```bash
# See how far behind/ahead a branch is relative to main
git fetch origin
git rev-list --left-right --count main...feature/my-branch
# Output: <commits-in-main-not-in-branch>  <commits-in-branch-not-in-main>

# Find the common ancestor
git merge-base main feature/my-branch
```
