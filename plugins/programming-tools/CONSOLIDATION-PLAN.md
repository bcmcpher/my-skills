# programming-tools Consolidation Plan

**Status:** Planned (not yet implemented)
**Date:** 2026-04-27

Consolidates four external tools into a combined local fork inside `plugins/programming-tools/`:

- **code-review-graph** — MCP server (server name: `code-review-graph` in `~/.mcp.json`); structural code intelligence tools: `semantic_search_nodes`, `get_impact_radius`, `get_affected_flows`, `get_review_context`, `get_architecture_overview`. Currently documented in root CLAUDE.md but not wired into agent tool lists.
- **superpowers** (v5.0.7, globally installed) — Fork: `test-driven-development` (Iron Law, rationalizations), `systematic-debugging` (4-phase root-cause), `verification-before-completion` (evidence before claims), `finishing-a-development-branch` (merge/PR workflow).
- **OpenSpec** (not installed) — Design from scratch as `/feature-spec` skill with ADR-style spec format.
- **andrej-karpathy-skills** (v1.0.0, globally installed) — Convert to shared plugin-level reference `references/karpathy-guidelines.md` loaded by all agents and skills.

---

## New Files to Create

| Path | Description |
|------|-------------|
| `references/karpathy-guidelines.md` | Adapted (not copied) from global karpathy skill — agent-oriented distillation with "Review Signals" section for what agents should flag |
| `skills/systematic-debug/SKILL.md` | Fork of superpowers systematic-debugging; Phase 1–4 process; references `/tdd` and `/verify` instead of superpowers equivalents; adds graph pre-pass in Phase 1 Step 4 |
| `skills/verify/SKILL.md` | Fork of superpowers verification-before-completion; claim-to-command mapping table up front; auto-invocable at end of `/tdd` and `/systematic-debug` |
| `skills/finish-branch/SKILL.md` | Fork of superpowers finishing-a-development-branch; 5-step process; option 2 references git-workflow's `commit-push-pr` format for PR body consistency |
| `skills/feature-spec/SKILL.md` | New OpenSpec-inspired skill; creates `docs/specs/YYYY-MM-DD-<slug>.md`; 5-phase workflow |
| `agents/security-reviewer/SKILL.md` | New OWASP Top 10 focused agent; model: opus; color: red; confidence ≥70 threshold; graph pre-pass to trace auth/input entry points |

### Feature-spec output format

```markdown
# Feature Spec: <name>
**Status:** Draft | Proposed | Accepted | Superseded
**Date:** YYYY-MM-DD

## Problem Statement
## Goals
## Non-Goals
## Acceptance Criteria   ← checkboxes; feed directly to /tdd
## Technical Approach
### Options Considered    ← table: Option | Pros | Cons | Status
### Decision Rationale
## Implementation Plan   ← phased tasks
## Open Questions        ← table: # | Question | Owner | Blocking
## Decision Log          ← table: Date | Decision | Rationale
## References
```

---

## Existing Files to Modify

### `skills/tdd/SKILL.md`
Add three new sections (do not remove anything):
1. **Iron Law block** after opening paragraph — "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"; delete-not-reference rule
2. **Common Rationalizations table** — 7-row table (adapted from superpowers)
3. **Verification Checklist** — 9-item checkbox list before "Core constraints"
4. In Phase 2 preamble: add one line loading `${CLAUDE_PLUGIN_ROOT}/references/karpathy-guidelines.md` for Simplicity First + Surgical Changes guidance

### All 6 existing agent SKILL.md files
Add to each body (after opening paragraph, before first section heading):
```markdown
## Behavioral guidelines
Apply `${CLAUDE_PLUGIN_ROOT}/references/karpathy-guidelines.md` when forming
recommendations: flag speculative additions (Simplicity First), verify changes
are surgical (Surgical Changes), and ensure success criteria are verifiable
(Goal-Driven Execution).
```

### `agents/code-reviewer/SKILL.md`
- Frontmatter `tools:` — add `mcp__code-review-graph__semantic_search_nodes`, `mcp__code-review-graph__get_impact_radius`, `mcp__code-review-graph__get_affected_flows`, `mcp__code-review-graph__get_review_context`
- Body — add "Pre-review graph query" section: run `get_review_context` on changed files, `get_impact_radius` to understand blast radius; fallback to Grep/Read if graph unavailable

### `agents/pr-test-analyzer/SKILL.md`
- Frontmatter: add `mcp__code-review-graph__get_affected_flows`, `mcp__code-review-graph__get_review_context`
- Body: add step 1a — run `get_affected_flows` on key changed functions to find integration paths needing coverage

### `agents/silent-failure-hunter/SKILL.md`
- Frontmatter: add `mcp__code-review-graph__get_affected_flows`, `mcp__code-review-graph__semantic_search_nodes`
- Body: pre-review section — `semantic_search_nodes` with "error handling", "exception", "catch" before reading individual blocks

### `agents/type-design-analyzer/SKILL.md`
- Frontmatter: add `mcp__code-review-graph__semantic_search_nodes`, `mcp__code-review-graph__get_review_context`
- Body: pre-review section — `semantic_search_nodes` to find all usages of reviewed type, surfacing invariant violations outside the diff

### `commands/code-check.md`
- After Step 1, add **Step 1b: graph pre-pass** — run `get_architecture_overview` once; pass summary as context to each delegated agent
- Add `security` row to routing table: dispatch `security-reviewer` when diff touches auth, passwords, tokens, file paths, network calls, or serialization (grep diff for: `auth`, `password`, `token`, `request.`, `open(`, `exec`, `subprocess`, `deserializ`)
- Add `Security Issues` section to aggregated report template
- Update aspect keyword table to include `security` → `security-reviewer`

### `.claude-plugin/plugin.json`
- Bump version `0.1.0` → `0.2.0`
- Update description
- Add to `skills`: `./skills/systematic-debug`, `./skills/verify`, `./skills/finish-branch`, `./skills/feature-spec`
- Add to `agents`: `./agents/security-reviewer`

### `README.md`
Full update: describe 6 skills, 7 agents, 1 command, references (6 language refs + karpathy-guidelines.md), note code-review-graph MCP dependency.

---

## Implementation Sequence

1. `references/karpathy-guidelines.md` first — all other files depend on it
2. Batch: all 5 new SKILL.md files (systematic-debug, verify, finish-branch, feature-spec, security-reviewer)
3. Batch: graph tool additions to agent frontmatter `tools:` fields (code-reviewer, pr-test-analyzer, silent-failure-hunter, type-design-analyzer)
4. Batch: karpathy guidelines instruction block into all 6 existing agent bodies
5. `/tdd` enhancements (Iron Law, rationalizations table, verification checklist, karpathy reference line)
6. `/code-check` command update (needs security-reviewer to exist first)
7. `plugin.json` last — after all referenced files exist
8. `README.md` update

---

## Gaps Remaining (Future Work)

| ID | Gap | Why deferred |
|----|-----|-------------|
| FW-1 | **Observability reviewer** — structured logging, trace IDs, metrics coverage | No agent today; needs dedicated design |
| FW-2 | **Performance reviewer** — algorithmic complexity, N+1 queries, hot-path regressions | Needs language-specific heuristics |
| FW-3 | **API design reviewer** — REST/GraphQL/RPC contract quality, versioning, backward compat | Distinct scope from code-reviewer |
| FW-4 | **Dependency audit skill** — CVE scanning, pinned vs. floating, license compat (`npm audit`, `pip-audit`, `cargo audit`) | Wraps external tools per language |
| FW-5 | **Accessibility reviewer** — ARIA, keyboard nav, WCAG | Narrow applicability; UI projects only |
| FW-6 | **`/subagent-dev` skill** — port superpowers subagent-driven-development to use `/feature-spec` output as input plan | Complex; defer until finish-branch + feature-spec are stable |
| FW-7 | **Mutation testing in `/tdd`** — verify tests catch synthetic bugs (`mutmut`, `stryker`) | Requires external tools per language |
| FW-8 | **Graph init skill** — detect stale/missing graph and guide `code-review-graph build` | May already be handled by hooks |

---

## Verification Checklist

```bash
# Valid JSON manifest with correct counts
python3 -m json.tool plugins/programming-tools/.claude-plugin/plugin.json
# Expect: 6 skills, 7 agents, 1 command

# Graph tools wired into agents
grep -r "mcp__code-review-graph" plugins/programming-tools/agents/
# Expect: code-reviewer, pr-test-analyzer, silent-failure-hunter,
#          type-design-analyzer, security-reviewer

# TDD enhancements present
grep -c "Iron Law\|Rationalization\|Verification Checklist" \
  plugins/programming-tools/skills/tdd/SKILL.md
# Expect: 3

# Karpathy reference in all agents
grep -rl "karpathy-guidelines" plugins/programming-tools/agents/
# Expect: all 6 agent directories

# Smoke test in live session
claude --plugin-dir ./plugins/programming-tools
# /help                           → 6 skills visible
# /feature-spec "test"            → creates spec file with all 7 sections
# /systematic-debug "test error"  → demands Phase 1 before proposing fix
# /code-check security            → dispatches security-reviewer
```
