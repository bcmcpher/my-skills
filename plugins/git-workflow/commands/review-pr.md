---
allowed-tools: Bash(gh issue view:*), Bash(gh search:*), Bash(gh issue list:*), Bash(gh pr comment:*), Bash(gh pr diff:*), Bash(gh pr view:*), Bash(gh pr list:*)
description: Review a GitHub pull request and post findings as a PR comment
argument-hint: <PR number or URL>
disable-model-invocation: false
---

Review the pull request identified by `$ARGUMENTS` (PR number or URL). If no argument is given, use the PR for the current branch: `gh pr view`.

Follow these steps precisely:

1. Use a Haiku subagent to check eligibility. Skip if the PR: (a) is closed, (b) is a draft, (c) is automated or trivially simple and needs no review, or (d) already has a review comment from a previous run.

2. Use a Haiku subagent to collect the paths of all relevant CLAUDE.md files: the root CLAUDE.md (if present) plus any CLAUDE.md files in directories touched by the PR diff.

3. Use a Haiku subagent to read the PR and return a plain-language summary of the change.

4. Launch 5 parallel Sonnet subagents to independently review the diff. Each returns a list of issues with the reason each was flagged:
   - Agent 1: Verify the changes comply with the instructions in the CLAUDE.md files gathered in step 2. Note: CLAUDE.md is written for code-writing sessions — not every rule applies to review.
   - Agent 2: Scan for obvious bugs. Read only the changed lines; do not explore surrounding context. Focus on significant bugs; ignore nitpicks and linter-catchable issues.
   - Agent 3: Read the git blame and commit history of the modified files; flag bugs that only make sense in light of that history.
   - Agent 4: Read prior PRs that touched these files and surface any prior review comments that also apply here.
   - Agent 5: Read code comments in the modified files and check whether the changes comply with any guidance embedded in those comments.

5. For each issue from step 4, launch a parallel Haiku subagent that scores confidence on a 0–100 scale:
   - 0: False positive, does not survive light scrutiny, or pre-existing issue
   - 25: Might be real but could not be verified; stylistic issues not explicitly in CLAUDE.md
   - 50: Verified as real, but minor or infrequent in practice
   - 75: Double-checked and very likely real; directly impacts functionality or is explicitly in CLAUDE.md
   - 100: Confirmed, will occur frequently, evidence is direct

6. Discard any issue scoring below 80. If none remain, do not post a comment.

7. Re-run the eligibility check from step 1 to confirm the PR is still open and eligible.

8. Post a comment on the PR using `gh pr comment`. Keep it brief, cite specific file locations, and avoid emojis.

**False positives to filter out:**
- Pre-existing issues not introduced by this PR
- Things that look like bugs but aren't
- Nitpicks a senior engineer would not raise
- Issues a linter, type-checker, or compiler catches (assume CI runs these)
- General quality issues (test coverage, docs, security) unless required by CLAUDE.md
- Issues silenced in code by a lint-ignore comment
- Intentional behavior changes directly related to the PR's stated purpose
- Real issues on lines the PR did not modify

**Comment format** (use exactly this structure):

```
### PR review

Found N issues:

1. <brief description> (CLAUDE.md says "<...>")

<https://github.com/OWNER/REPO/blob/FULL_SHA/path/to/file.ext#L10-L14>

2. <brief description> (bug due to <file and snippet>)

<https://github.com/OWNER/REPO/blob/FULL_SHA/path/to/file.ext#L22-L26>

🤖 Generated with [Claude Code](https://claude.ai/code)
```

Or, if no issues:

```
### PR review

No issues found. Checked for bugs and CLAUDE.md compliance.

🤖 Generated with [Claude Code](https://claude.ai/code)
```

**Link format rules:**
- Always use the full 40-character SHA — never `HEAD` or a branch name
- URL format: `https://github.com/OWNER/REPO/blob/SHA/path#L{start}-L{end}`
- Include at least one line of context before and after the flagged line(s)
- Repo name must match the repo being reviewed
