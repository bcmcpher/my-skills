---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
description: Stage and commit all changes with a conventional commit message
---

## Context

- Current git status: !`git status`
- Staged changes (will be committed): !`git diff --cached`
- Unstaged changes (not yet staged): !`git diff`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Your task

Based on the above changes, create a single git commit.

Rules:
- Subject line: imperative mood, ≤72 characters (e.g. `Add retry logic to upload handler`)
- Body: explain *why*, not *what* — the diff shows what
- Always append the trailer on its own line after a blank line:
  `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`
  *(Update the model name here when upgrading Claude versions.)*
- One logical change per commit; if the diff mixes unrelated changes, stage only the relevant files

Stage and create the commit in a single message. Do not use any other tools or send any other text.
