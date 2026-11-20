# Writing agents

Status: draft, revised 2026-11-19. Not started. Phase 1 (the technical-docs writer) is
specified below, its decisions are settled, and it is ready to execute. Phase 2 (the manuscript
writer) is a stub.

The old blocker is resolved: the ASD-STE100 vocabulary lives at
`~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf`, outside the repo. A script reads the dictionary
from that PDF on the user's machine. The user holds the PDF under a qualified use, so a local
derived lexicon is in scope. The repo still never holds the dictionary or a copy of it, because
the repo is meant to become public.

The config-reconcile work that once shared this plan is done. Its record is in the git history of
`plans/config-reconcile-and-writing-agents.md` (last version before 2026-11-09).

## Goal

Two writing agents, each separate from the `writing.md` fallback, which stays in the global
config:

1. **technical-docs-writer** — writes and revises technical documentation at about 80% of
   ASD-STE100 Simplified Technical English (STE), the same level as `writing.md`. The aim is
   consistent phrasing and descriptions, and catching jargon leaks — not full STE compliance. It
   checks its output with a deterministic checker that works with any dictionary in a common
   format. On request, it classifies a document by the documentation quadrants and proposes a
   split.
2. **manuscript-writer** — drafts and edits grants and manuscripts in the user's professional
   voice. Phase 2.

## Phase 1: technical-docs-writer

### Pieces

A new plugin, `plugins/tech-docs/`. The manuscript writer gets its own plugin later, because the
two tasks share almost no references.

```
plugins/tech-docs/
├── .claude-plugin/plugin.json
├── agents/technical-docs-writer/SKILL.md   # the agent: write, revise, self-check
├── skills/ste-check/
│   ├── SKILL.md                             # build a lexicon, run the checker, read its report
│   ├── references/lexicon-format.md         # the common lexicon format
│   └── scripts/
│       ├── lexicon.py                       # source dictionary → common lexicon
│       └── ste_check.py                     # promoted from evaluations/2026-10-08-ste-docs/
├── skills/doc-quadrants/
│   ├── SKILL.md                             # classify, propose a split, audit a doc set
│   └── references/quadrants.md              # our own summary of the model
└── tests/                                   # synthetic fixtures only; no dictionary text
```

### 1. Common lexicon format

The checker reads one format, and it knows nothing about STE or PDFs. Any dictionary can feed
it. `references/lexicon-format.md` documents the format. A lexicon is a JSON file:

- `name` — a label for reports, for example `ste100-issue9`.
- `closed` — `true` when the approved entries are a complete vocabulary, as in STE. Only a closed
  lexicon enables the `jargon` flag, because only then does "not in the list" mean something.
  A replacement list, such as a personal list of words to avoid, is open.
- `entries` — each with `term` (one word or a phrase), optional `pos`, `approved` (true or false),
  optional `kind` (`TN` or `TV`, for a declared technical noun or verb), optional `forms` (the
  permitted inflections), and, for a term that is not approved, `alternatives` (each a term, an
  optional `pos`, and an optional kind).

The checker takes `--lexicon` more than once. Lexicons stack, and a later one overrides an
earlier one for the same term. A user can then layer a project list on top of STE.

#### Declared technical terms

A project can declare its technical terms up front: the product names, tools, file formats and
domain nouns that its docs must use. The declared list is the jargon input. It is an open lexicon
of approved entries with kind `TN` or `TV`, so the checker needs no second mechanism for it.

- File: `.tech-terms` at the project root, found automatically, or `--terms <file>`. One term per
  line, written in its canonical spelling, with an optional `<TAB>TV` for a verb (`TN` is the
  default). `#` starts a comment.
- The project glossary feeds the same list. The checker reads each defined term from
  `GLOSSARY.md`, `docs/glossary.md`, or a "Key terms" section. The glossary stays the place where
  a term is defined; `.tech-terms` is the lighter option for a project with no glossary.
- `.tech-terms` replaces the `.ste-allow` allowlist of the earlier draft.

Write the list from the source material — code, `plugin.json`, the domain — not from the docs
that the checker will score. A list built from the output makes the leak count circular.

### 2. Lexicon builder (`lexicon.py`)

Deterministic, stdlib Python. It converts a source dictionary into the common format. Two
sources at first:

- `lexicon.py build --from tsv <file>` — a hand-written list, one entry per line:
  `term<TAB>replacement[<TAB>pos]`. An empty replacement marks an approved term. This makes the
  tool useful for any plain-language word list, not only STE.
- `lexicon.py build --from ste-pdf [<pdf>]` — the ASD-STE100 adapter, described below.

Output goes to `${XDG_DATA_HOME:-~/.local/share}/tech-docs/lexicons/<name>.json` by default. The
builder refuses an output path inside a git work tree, so a licensed lexicon cannot be committed
by mistake.

#### The STE adapter

It uses `pdftotext -layout` (poppler; already on this machine).

- Input path: the argument, else `$STE100_PDF`, else
  `~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf`.
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

### 3. Checker (`ste_check.py`)

Promote the evaluation checker into the plugin. The evaluation keeps a pointer to the new path
rather than its own copy. Keep the current rules (`length`, `passive`, `ing`, `hedge`,
`multi-instruction`, paragraph length). Its hard-coded `NON_APPROVED` list becomes a small
built-in open lexicon in the common format. Add the dictionary rules when a lexicon is loaded:

| Flag | Meaning | Report |
|---|---|---|
| `word` | Term listed as not approved | The approved alternatives from the lexicon |
| `form` | Inflection not listed for an approved term (for example `-ing` of an approved verb) | The listed forms |
| `jargon` | Word in no loaded lexicon and not a declared term (closed lexicons only) | A leak: an undeclared term, or a word to replace |
| `variant` | One term written two ways in the same doc set | Both spellings, their counts, and the declared spelling if there is one |

`variant` serves the consistency goal. It is deterministic: it groups words that are equal after
removing case, hyphens and spaces (`code graph`, `code-graph`, `codegraph`). When one spelling is
a declared term, the report names it as correct; otherwise it names no winner. It also flags a doc
that uses both a non-approved term and its approved alternative, so the same idea appears in two
words. A `pos` check for rule 1.2 needs a part-of-speech tagger, so it stays out.

**The checker is a soft audit.** It always exits 0, and it reports; it never blocks. The score
target is about 80%, the `writing.md` level, not 100%. Concise technical docs cannot avoid
jargon, so the jargon report is a list to review, not a list to eliminate.

The `jargon` flag is the jargon finder. STE rules 1.5 and 1.12 permit technical nouns and verbs
that are not in the dictionary. The declared terms separate the permitted ones from the leaks:

1. A word in the dictionary, or a declared term: accepted. No flag.
2. Any other word: a leak. Report it with its count and first location, most frequent first.
   `--jargon` prints only this list, so the agent or user can triage each leak: declare it,
   define it in the glossary, or rewrite it. A frequent leak probably needs declaring. A leak
   used once is the likeliest unplanned term.

The report also states how many hits each declared-term source suppressed. A list that hides a
large share of all hits is too broad, and the count makes that visible.

With no declared terms, the checker still runs `jargon`, but every technical term then appears
as a leak. The report says so, and suggests a `.tech-terms` file.

This ties the checker to the existing `writing.md` rule that every technical term goes in the
glossary.

Morphology stays simple and deterministic: lowercase, strip plural `-s`/`-es` for nouns, and
match verb forms only against the forms the dictionary lists. Code spans, fences, link targets and
headings are stripped first, as now.

Without a closed lexicon, the checker runs the other rules and says that `jargon` is off. This
keeps CI and other machines working, because CI never has the PDF.

### 4. Quadrants skill (`doc-quadrants`)

Source: Daniele Procida's documentation framework (Diátaxis), as summarized by Steve Dunn,
<https://dunnhq.com/posts/2023/documentation-quadrants/>. `references/quadrants.md` is our own
summary with both links. It does not copy either text.

The model, as the skill uses it. The fourth quadrant is "Explanation" (the Diátaxis name)
everywhere in the plugin. Dunn calls it "Discussion"; the reference notes that alias once.

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

### 5. The agent (`technical-docs-writer`)

An agent rather than a skill, because whole-document passes suit an isolated context.

- Model: `inherit` (the session's model) for now.
- Tools: Read, Grep, Glob, Bash (for the checker), Edit, Write.
- Workflow: read the target, the project glossary and `.tech-terms` → write or revise, using the
  declared terms in their declared spelling → run `ste_check.py` → fix flagged sentences until
  the score is about 80% → triage `jargon` and `variant` hits (declare, define in the glossary,
  or rewrite) → report the score, the open hits, and any terms it suggests declaring.
- The agent proposes additions to `.tech-terms`; it does not add them itself. Otherwise it could
  silence its own leaks.
- New files: the agent writes them directly. Existing files: it delivers a diff for the user to
  apply, as `engineering.md` requires for hand-curated files.
- Precedence: a project's own documentation style overrides the agent, as with `writing.md`.
- Does not apply to manuscripts, grants, spec artifacts, or chat replies.

### 6. Evaluation

Extend `evaluations/2026-10-08-ste-docs/` rather than starting a new one:

- **STE A/B.** Three arms on the same prompt: base, `writing.md`, and the agent. Score with the
  full checker (STE lexicon on). Same n=3 and tmux procedure as the existing harness.
- **Quadrant classification.** Hand-label the sections of 3–4 existing READMEs
  (`config/README.md` is a known mix). Compare the skill's labels against them.
- **Declared terms for the A/B.** Before the runs, write a `.tech-terms` list for the target
  plugin from its code and `plugin.json`. All arms receive the same list in the prompt context.
  Two new measures per arm, beside the score:
  - **leak rate:** `jargon` hits per 100 words;
  - **term coverage:** the share of declared terms that the output uses where it describes that
    thing, in the declared spelling, rather than a paraphrase or a `variant`.
- **Jargon detection.** Plant known leaks (undeclared terms, non-approved words, spelling
  variants) in a synthetic fixture doc, and count how many the checker catches. Repeat with the
  declared list removed, to show what the list adds.
- **Jargon precision.** On two READMEs with a declared list, check by hand what fraction of the
  remaining `jargon` hits are real leaks.

### Success criteria

- `lexicon.py build --from ste-pdf` reproduces 875 approved and 1274 non-approved words from
  Issue 9.
- `lexicon.py build --from tsv` and the checker work on a synthetic open lexicon with no STE
  input. `jargon` stays off for it.
- No dictionary text, lexicon file or extract is in the repo. `bin/graduate tech-docs` passes.
- The checker runs with and without a lexicon, and always exits 0. Tests use synthetic lexicon
  fixtures.
- The checker finds every planted leak in the fixture doc when the declared list is loaded.
- The agent arm scores at least as high as the `writing.md` arm, and keeps the same key facts.
  Its leak rate is no higher, and its term coverage no lower.
- On the hand-labelled READMEs, the quadrants skill agrees with the labels on most sections.

### Decisions (settled 2026-11-19)

1. **Licensing:** the user holds the PDF under a qualified use. A local derived lexicon is in
   scope. Derived files still stay out of the repo.
2. **Dictionary scope:** the checker works with any dictionary in the common lexicon format. STE
   is one source. The audit is soft: it reports and never blocks, because concise docs cannot
   avoid jargon.
3. **Strictness:** about 80% of STE, the `writing.md` level. The goal is consistent phrasing and
   descriptions, and catching jargon leaks.
4. **Quadrant name:** Explanation.
5. **Existing docs:** new files are written directly; existing files get a diff.
6. **Layout:** separate plugins, `tech-docs` now and `manuscript` later.
7. **Model:** inherit the session's model for now.
8. **Declared terms:** a project can declare its technical terms up front in `.tech-terms`. The
   list separates permitted terms from leaks, sets the canonical spelling for `variant`, and
   gives the evaluation its leak rate and term coverage measures.

### Execution order

Each step ends in a commit on `plan/writing-agents`:

1. Common lexicon format, `lexicon.py --from tsv`, and synthetic fixtures with tests.
2. The STE adapter, checked against the 875/1274 counts on the local PDF.
3. Promote `ste_check.py`; add `word`, `form`, `jargon`, `variant`, and the declared terms
   (`.tech-terms`, `--terms`, glossary) with their suppression counts.
4. The `doc-quadrants` skill and its reference.
5. The agent, `plugin.json`, README, and `bin/graduate tech-docs`.
6. The evaluation extensions and their results.

## Phase 2: manuscript-writer (stub)

It drafts and edits grants, manuscripts and other professional prose in the user's voice. It
never edits the draft directly: it delivers paste-able text or a diff (the fwdti rule). Start
after Phase 1 ships. Open:

- the style source: journal guides, or the user's past papers;
- the handling of citations, through `zotero-cli` and `opencite`;
- whether it shares anything with Phase 1, for example the hedge and length checks.

Relation to caveman: none for either agent. They write files, not chat.
