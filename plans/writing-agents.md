# Writing agents

Status: draft, revised 2026-11-19. Not started. Phase 1 (the technical-docs writer) is
specified below and ready to execute after the open decisions are answered. Phase 2 (the
manuscript writer) is a stub.

The old blocker is resolved: the ASD-STE100 vocabulary lives at
`~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf`, outside the repo. A script reads the dictionary
from that PDF on the user's machine. The repo never holds the dictionary or a copy of it.

The config-reconcile work that once shared this plan is done. Its record is in the git history of
`plans/config-reconcile-and-writing-agents.md` (last version before 2026-11-09).

## Goal

Two writing agents, each separate from the `writing.md` fallback, which stays in the global
config:

1. **technical-docs-writer** — writes and revises technical documentation in ASD-STE100
   Simplified Technical English (STE). It checks its output with a deterministic STE checker. On
   request, it classifies a document by the documentation quadrants and proposes a split.
2. **manuscript-writer** — drafts and edits grants and manuscripts in the user's professional
   voice. Phase 2.

## Phase 1: technical-docs-writer

### Pieces

A new plugin, `plugins/tech-docs/` (name open, see decisions):

```
plugins/tech-docs/
├── .claude-plugin/plugin.json
├── agents/technical-docs-writer/SKILL.md   # the agent: write, revise, self-check
├── skills/ste-check/
│   ├── SKILL.md                             # run the checker, read its report
│   └── scripts/
│       ├── ste_lexicon.py                   # PDF → local lexicon (one-time build)
│       └── ste_check.py                     # promoted from evaluations/2026-10-08-ste-docs/
├── skills/doc-quadrants/
│   ├── SKILL.md                             # classify, propose a split, audit a doc set
│   └── references/quadrants.md              # our own summary of the model
└── tests/                                   # synthetic fixtures only; no dictionary text
```

### 1. Lexicon builder (`ste_lexicon.py`)

Deterministic. Stdlib Python plus `pdftotext -layout` (poppler; already on this machine).

- Input: the PDF. Path from `--pdf`, else `$STE100_PDF`, else
  `~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf`.
- Output: `${XDG_DATA_HOME:-~/.local/share}/ste100/lexicon-issue9.json`, never inside a repo.
  The builder refuses an output path inside a git work tree.
- Parse only the dictionary pages, whose footers read `Page 2-1-<letter><n>` (for example
  `Page 2-1-V3`). The changelog and the introduction (`2-0-*`) repeat entries and must not count.
- Headwords can be multi-word (`brush on (v)`, `in order to`). Match phrases before single words.
- Column 1 rule, from the dictionary introduction: an UPPERCASE headword is approved, a
  lowercase headword is not approved. Part of speech is in parentheses: `n v adj adv pron art
  prep conj`.
- Per entry, record: headword, part of speech, approved flag, listed forms (verb forms such as
  `ADAPTS, ADAPTED`; adjective comparatives in parentheses), and, for a non-approved word, its
  approved ALTERNATIVES from column 2 with their part of speech. `(TN)` and `(TV)` alternatives
  are tagged as technical nouns or technical verbs.
- Do not store the example columns. The checker does not need them, and leaving them out keeps
  the derived file minimal.
- Acceptance check: the introduction states 875 approved words and 1274 non-approved words. The
  builder prints its counts, and it exits non-zero when they differ.

A first probe (2026-11-19) found that the text extracts cleanly despite the PDF's copy flag. The
column layout survives: `ensure (v)   MAKE SURE (v)`, `via (prep)   THROUGH (prep)`.

### 2. Checker (`ste_check.py`)

Promote the evaluation checker into the plugin. The evaluation keeps a pointer to the new path
rather than its own copy. Keep the current rules (`length`, `passive`, `ing`, `hedge`,
`multi-instruction`, paragraph length). Add the dictionary rules when a lexicon is present:

| Flag | Meaning | Report |
|---|---|---|
| `word` | Headword listed as not approved | The approved alternatives from the lexicon |
| `pos` | Approved word, probably used as a different part of speech (rule 1.2) | Low confidence; off by default |
| `form` | Verb form not listed for an approved verb (for example `-ing` of an approved verb) | The listed forms |
| `jargon` | Word not in the dictionary at all | A candidate technical noun or verb, or a word to replace |

The `jargon` flag is the jargon finder the user asked for. STE rules 1.5 and 1.12 permit
technical nouns and verbs that are not in the dictionary. So a `jargon` hit is a question, not an
error. Resolve it in this order:

1. The word is in the project glossary (`GLOSSARY.md`, `docs/glossary.md`, or a "Key terms"
   section). It is an accepted technical term. Suppress it.
2. The word is in a project allowlist (`.ste-allow`, one word per line). Suppress it.
3. Otherwise, report it with its count and first location. `--jargon` prints only this list, so
   the agent or user can triage it into the glossary or a rewrite.

This ties the checker to the existing `writing.md` rule that every technical term goes in the
glossary.

Morphology stays simple and deterministic: lowercase, strip plural `-s`/`-es` for nouns, and
match verb forms only against the forms the dictionary lists. Code spans, fences, link targets and
headings are stripped first, as now.

Without a lexicon, the checker runs the rule subset as now and says so in its output. This keeps
CI and other machines working, because CI never has the PDF.

### 3. Quadrants skill (`doc-quadrants`)

Source: Daniele Procida's documentation framework (Diátaxis), as summarized by Steve Dunn,
<https://dunnhq.com/posts/2023/documentation-quadrants/>. `references/quadrants.md` is our own
summary with both links. It does not copy either text.

The model, as the skill uses it:

| Quadrant | Serves | Contains | Keeps out |
|---|---|---|---|
| Tutorial | Study, practical | A guided path to an outcome the author chooses | Concept explanations, options |
| How-to guide | Work, practical | Steps to solve one named problem | Basics from the tutorial |
| Reference | Work, theoretical | Complete, consistent facts about each component | Instructions, concepts |
| Explanation | Study, theoretical | Background, design reasons, how ideas connect | Instructions, component detail |

Three modes. The agent uses them only when the user asks:

1. **Classify.** Label each section of a document with a quadrant and one line of evidence. Mark
   a section as mixed when it collapses two quadrants, for example a concept paragraph inside
   numbered steps.
2. **Propose a split.** Output a file plan: new file names (how-to files named by task, such as
   `how-to-validate-input.md`), which sections move where, and a short landing page that routes
   readers to each quadrant. It is a proposal. The agent edits nothing until the user approves.
3. **Audit a doc set.** For a directory, report which quadrants exist, which are missing, and
   which files are mixed.

STE applies to all four quadrants. Procedural rules dominate tutorials and how-to guides, and
descriptive rules dominate reference and explanation.

### 4. The agent (`technical-docs-writer`)

An agent rather than a skill, because whole-document passes suit an isolated context.

- Tools: Read, Grep, Glob, Bash (for the checker), Edit, Write.
- Workflow: read the target and the project glossary → write or revise → run `ste_check.py` →
  fix flagged sentences until the score target holds → triage `jargon` hits (glossary, allowlist
  or rewrite) → report the score and the open `jargon` list.
- Precedence: a project's own documentation style overrides the agent, as with `writing.md`.
- Does not apply to manuscripts, grants, spec artifacts, or chat replies.

### 5. Evaluation

Extend `evaluations/2026-10-08-ste-docs/` rather than starting a new one:

- **STE A/B.** Three arms on the same prompt: base, `writing.md`, and the agent. Score with the
  full checker (lexicon on). Same n=3 and tmux procedure as the existing harness.
- **Quadrant classification.** Hand-label the sections of 3–4 existing READMEs
  (`config/README.md` is a known mix). Compare the skill's labels against them.
- **Jargon precision.** On two READMEs, check by hand what fraction of `jargon` hits are true
  technical terms, and what fraction are words that need replacing.

### Success criteria

- `ste_lexicon.py` reproduces 875 approved and 1274 non-approved words from Issue 9.
- No dictionary text, lexicon file or extract is in the repo. `bin/graduate tech-docs` passes.
- The checker runs with and without a lexicon. Tests use a synthetic lexicon fixture.
- The agent arm scores at least as high as the `writing.md` arm, and keeps the same key facts.
- On the hand-labelled READMEs, the quadrants skill agrees with the labels on most sections.

### Open decisions

1. **Licensing.** The ASD copyright notice restricts reproduction in whole or in part. A derived
   lexicon on the user's own machine, built from the user's own copy, seems within personal use,
   but the user decides that. The plan keeps every derived file out of the repo either way.
2. **STE strictness.** Full STE (dictionary words only, plus glossary terms), or the `writing.md`
   level of about 80%? This sets the agent's score target.
3. **Quadrant names.** Diátaxis uses "Explanation". Dunn uses "Discussion". Pick one and use it
   everywhere. Recommended: Explanation, the more widely known term.
4. **Editing existing docs.** May the agent edit an existing document directly, or does it
   deliver a diff, as for hand-curated files (`engineering.md`)? Recommended: it writes new files
   directly, and it delivers a diff for files that already exist.
5. **Plugin name and layout.** One plugin per agent (`tech-docs` now, `manuscript` later), or one
   `writing` plugin with both? Recommended: separate plugins, because the two share almost no
   references.
6. **Model.** Inherit, or pin one.

## Phase 2: manuscript-writer (stub)

It drafts and edits grants, manuscripts and other professional prose in the user's voice. It
never edits the draft directly: it delivers paste-able text or a diff (the fwdti rule). Start
after Phase 1 ships. Open:

- the style source: journal guides, or the user's past papers;
- the handling of citations, through `zotero-cli` and `opencite`;
- whether it shares anything with Phase 1, for example the hedge and length checks.

Relation to caveman: none for either agent. They write files, not chat.
