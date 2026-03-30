---
allowed-tools: Bash(git checkout:*), Bash(git add:*), Bash(git status:*), Bash(git push:*), Bash(git commit:*), Bash(git branch:*), Bash(gh pr create:*)
description: Commit, push, and open a pull request
---

## Context

- Current git status: !`git status`
- Current git diff (staged and unstaged changes): !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Your task

Based on the above changes:

1. If currently on `main` or `master`, create a new branch with a descriptive kebab-case name
2. Create a single commit with a conventional message:
   - Subject line: imperative mood, ≤72 characters
   - Body: explain *why*, not *what*
   - Always append the trailer on its own line after a blank line:
     `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
3. Push the branch to origin with `-u` to set tracking
4. Create a pull request using `gh pr create` with a clear title and body

Do all of the above in a single message. Do not use any other tools or send any other text.
