# Writing-style agents

Status: draft, 2026-10-08. Not started. Blocked on one decision: where the ASD-STE100
vocabulary lives (see agent 2).

The config-reconcile work that shared this plan is done. Its record is in the git history of
`plans/config-reconcile-and-writing-agents.md` (last version before 2026-11-09).

## Goal

Add two dedicated writing passes, separate from the `writing.md` fallback. `writing.md` stays in
the global config.

## Agents

1. **Scientific manuscript agent.** It edits or drafts manuscript and grant prose in the user's
   voice. It never edits the draft directly: it delivers paste-able text or a diff (the fwdti
   rule). Open:
   - the style source: journal guides, or the user's past papers;
   - the handling of citations. `zotero-cli` and `opencite` are available.
2. **ASD-STE100 agent.** It rewrites technical docs to Simplified Technical English (STE). The
   user provides the approved vocabulary.
   - The vocabulary is ASD-licensed. Keep it out of this repo, which is meant to become public.
     Load it from a local path. **Open: which path.**
   - When the vocabulary is available, add a dictionary check to
     `evaluations/2026-10-08-ste-docs/ste_check.py`. The checker then becomes the agent's
     self-check.
   - Measure with the existing A/B harness: the `writing.md` fallback against the agent.

## Open for both

- Agent or skill form. Agents get an isolated context, which suits whole-document passes.
- Which model.
- Relation to caveman: none. The agents write files, not chat.
