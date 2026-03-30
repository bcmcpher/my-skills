---
description: Run a pre-commit code review using specialized agents against local git changes
argument-hint: [aspects] — e.g. "code errors" or "tests comments" or "all"
allowed-tools: Bash(git diff:*), Bash(git status:*), Bash(git log:*), Glob, Grep, Read, Task
---

# Pre-commit code check

Run a targeted review of local uncommitted changes using specialized agents. Each agent
focuses on a specific quality dimension.

**Review aspects requested:** "$ARGUMENTS" (default: all applicable)

---

## Step 1 — Identify changed files

```bash
git diff --name-only
git status --short
```

Parse `$ARGUMENTS` to determine which aspects to run. If empty or "all", run all
applicable aspects.

## Step 2 — Determine applicable agents

| Aspect keyword | Agent | Applicable when |
|---|---|---|
| `code` | code-reviewer | Always |
| `tests` | pr-test-analyzer | Test files are present in the diff |
| `comments` | comment-analyzer | Comments or docstrings added/modified |
| `errors` | silent-failure-hunter | Error handling, catch blocks, or fallback logic changed |
| `types` | type-design-analyzer | New types or type definitions added |
| `simplify` | code-simplifier | After other reviews pass — polish only |

Always run `code-reviewer`. Run the others based on what the diff contains, or when
explicitly requested via `$ARGUMENTS`.

## Step 3 — Run agents

**Sequential** (default): run one agent at a time for easier triage.

**Parallel** (if user includes "parallel" in `$ARGUMENTS`): launch all selected agents
simultaneously.

Each agent reads the diff independently and returns its findings.

## Step 4 — Aggregate results

Organize all findings into a single report:

```markdown
# Code Check Report

## Critical Issues (must fix before commit)
- [agent-name]: Issue description [file:line]

## Important Issues (should fix)
- [agent-name]: Issue description [file:line]

## Suggestions (nice to have)
- [agent-name]: Suggestion [file:line]

## Strengths
- What's well-done in this change

## Recommended action
1. Fix critical issues
2. Address important issues
3. Consider suggestions
4. Re-run /code-check after fixes
```

---

## Usage examples

**Full review (default):**
```
/code-check
```

**Specific aspects:**
```
/code-check code errors
/code-check tests
/code-check comments types
```

**Parallel review:**
```
/code-check all parallel
```

**Polish after passing review:**
```
/code-check simplify
```

---

## Workflow integration

**Before committing:**
1. Write code and get tests green
2. Run `/code-check` (or `/code-check code errors`)
3. Fix critical issues
4. Run `/commit`

**Before creating a PR:**
1. Run `/code-check all`
2. Address critical and important issues
3. Run `/code-check simplify` for a final polish pass
4. Run `/commit-push-pr`

---

## Notes

- Agents analyze `git diff` by default — only changed code is reviewed
- `code-simplifier` runs last by design: it polishes code that has already passed review
- Re-run after fixes to verify issues are resolved
- For GitHub PR review after pushing, use `/review-pr` from the git-workflow plugin
