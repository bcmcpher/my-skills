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

First, check whether there are any uncommitted changes:
- If `git status` shows a clean working tree and the branch already has commits
  ahead of its upstream (or has no upstream yet), skip to step 3 (push) — there
  is nothing new to commit.
- If there are uncommitted changes, proceed from step 1.

1. If currently on `main` or `master`, create a new branch with a descriptive kebab-case name
2. Create a single commit with a conventional message:
   - Subject line: imperative mood, ≤72 characters
   - Body: explain *why*, not *what*
   - Always append the trailer on its own line after a blank line:
     `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
     *(Update the model name here when upgrading Claude versions.)*
3. Push the branch to origin with `-u` to set tracking
4. Check for a PR template:
   ```bash
   cat .github/PULL_REQUEST_TEMPLATE.md 2>/dev/null
   ```
   If found, use it as the structure for the PR body, filling in each section.
   If not found, write a clear title and body summarizing the change and its purpose.
5. Create the pull request:
   ```bash
   gh pr create --title "<title>" --body "$(cat <<'EOF'
   <body>
   EOF
   )"
   ```
   To open as a draft (work in progress, not ready for review), add `--draft`.

Do all of the above in a single message. Do not use any other tools or send any other text.
