# A citekey-keyed plain-text export of the Zotero library

*Draft plan — 2026-09-03. Not yet approved or started.* Extended 2026-09-04 with findings
from a live trial (second half of this file), which correct several claims made above them.
This is the canonical copy; `~/.claude/plans/i-would-like-to-foamy-crown.md` is the earlier
draft, without the addendum.

## Context

The Zotero library (1767 top-level items, 1530 PDFs on disk, 2084 storage dirs) is the primary
catalog of source documents and is already integrated into drafts via Better BibTeX. The goal is a
standardised, machine-ingestible decomposition of each source: markdown full text, a BibTeX file of
that paper's own reference list, and enough provenance to feed a vector store, a graph DB, a memex
vault, or a harness session — without re-deriving any of it per use.

The assumption going in was that this needed a dedicated Zotero plugin. It does not. Probing the
installed tools showed the expensive part is already solved, and the missing pieces are small.

### What the probe established

**A high-quality PDF→markdown extractor is already installed and working.** `zotero-mcp-server`
hard-depends on `pdf-inspector` 0.2.6 (a Rust parser, no Python deps, prebuilt wheels), reached via
`zotero_mcp.extract.extract_pdf` and surfaced as `zotero-cli read`. On a random sample of 8 library
PDFs spanning 2004–2026:

| pages | time | tables | columns | needs OCR | chars |
|---|---|---|---|---|---|
| 7–143 | **39–463 ms** | 0–44 | 4–43 | **0** | 24k–283k |

All 8 were `text_based` with zero OCR pages. Full-library extraction is **~4 minutes of CPU**, and
the output carries real heading structure, bold/italic, tables and links. Its API also exposes
`extract_text_with_positions` (per-item font, size, bbox, page) and `extract_text_in_regions`,
which is what makes figure-caption extraction tractable later.

**Better BibTeX is live and scriptable.** JSON-RPC at `http://localhost:23119/better-bibtex/json-rpc`
answers `item.citationkey` in bulk, mapping Zotero item keys to the real citekeys used in drafts
(format `auth.lower + shorttitle(3,3) + year`, e.g. `livint-popaSelectiveNeuronalVulnerability2026`).

**opencite supplies reference lists from APIs, not PDF parsing.**
`opencite cite <doi> --direction references -f bibtex` returns clean BibTeX. 1528 of 1767 items
(86%) carry a DOI, so this path covers most of the library.

### What the probe found broken

1. **`opencite convert` fails on every PDF.** opencite's `[pdf]` extra declares `markitdown>=0.1.0`
   instead of `markitdown[pdf]`, so `pdfminer-six` and `pdfplumber` were never installed. Every
   conversion dies with `PdfConverter threw MissingDependencyException`. The extra was taken in the
   previous plan specifically to enable this, and it never worked. Upstream bug #3.
2. **`zotero-cli outline` fails.** Needs PyMuPDF; the intent file pins bare `zotero-mcp-server`
   rather than `zotero-mcp-server[pdf]`.
3. **Zotero cannot be written to.** The local API is read-only (`PATCH /api/users/0/items/<k>` →
   `501`) and `ZOTERO_API_KEY` is unset. No programmatic rename, tagging, or attaching is possible.
4. **No citekeys are pinned.** 0 of 1767 items carry `Citation Key:` in Extra, so BBT keys are
   dynamic and can drift if metadata changes — which would silently rename directories in the
   export tree on a later run.

### Decisions taken

| Decision | Choice |
|---|---|
| Export root | `~/Zotero/derived/`, git-ignored, treated as regenerable |
| First pass | Pilot collection, then decide on the full run |
| Zotero write-back | Not now — read-only until the pipeline is proven; long-term goal |
| On-disk renaming | User-driven through the Zotero UI (see below), out of scope for the code |
| Extraction engine | `pdf-inspector`, not markitdown |

## Answering the renaming question

Yes — this is entirely doable from the Zotero UI, and it is the *only* safe way given finding 3.
Zotero 9.0.6 handles the database and the file together; anything external would desynchronise them.

- **Edit the template:** Settings → General → **File Renaming** → **Configure File Renaming…**
  (`preferences-file-renaming-title`, `preferences-file-renaming-configure-button`). The template
  is stored as `extensions.zotero.attachmentRenameTemplate`, currently unset, i.e. Zotero's default
  `{{ firstCreator }}-{{ year }}-{{ title }}`.
- **Apply retroactively:** select any number of items in the middle pane → right-click →
  **Rename Files from Parent Metadata** (`pane.items.menu.renameAttachments.multiple`).

Do that whenever you like; it is independent of everything below. The export tree is keyed by BBT
citekey and records the attachment key, so renaming before, during, or after a run changes nothing —
`index.jsonl` re-resolves paths on the next run.

For reference, current state across 1548 PDFs: 1088 ZotFile-era `A - Y - T`, 121 Zotero-default
`A-Y-T`, 210 mixed legacy, 91 publisher junk (`nn.4134.pdf`), 38 year-first
(`2025.12.20.695692v1.full.pdf`).

## Stage 0 — repair the tool environment

Two one-line edits to `config/tools/python-tools.txt`, each with a comment recording the failure it
fixes (matching the file's existing style):

- `zotero-mcp-server` → `zotero-mcp-server[pdf]` — pulls PyMuPDF. Fixes `zotero-cli outline`, and
  unlocks figure *image* extraction later without any API key.
- add `markitdown[pdf]` as a separate constraint line — repairs `opencite convert`. Keep
  `opencite[pdf]`; the extra still supplies `markit-mistral` and the preprint HTML routes.

Then `bin/rebuild-tools`, `bin/rebuild-tools --freeze`, `bin/rebuild-tools --check`. Update
`config/README.md`'s opencite section with the `markitdown[pdf]` finding, since it directly
contradicts the rationale recorded there.

Not on the critical path — `pdf-inspector` is the extraction engine and already works — but both are
currently-broken commands that the config claims are working.

## Stage 1 — the export pipeline (pilot)

New plugin `plugins/refs-pipeline/`, following the repo's anatomy:

```
plugins/refs-pipeline/
├── .claude-plugin/plugin.json
├── README.md
├── references/
│   └── zotero-access.md          # local API shape, BBT RPC, read-only constraint
└── skills/
    ├── refs-export/
    │   ├── SKILL.md
    │   └── scripts/refs_export.py
    └── refs-audit/
        └── SKILL.md              # reads index.jsonl + report.md, no extraction
```

### Output layout

```
~/Zotero/derived/
├── library.bib               # whole library, one BBT export
├── doi-to-citekey.json       # DOI → BBT citekey, for the whole library
├── index.jsonl               # one line per exported item
├── report.md                 # pilot metrics
└── refs/<citekey>/
    ├── <citekey>.md          # YAML frontmatter + full text
    ├── <citekey>.bib         # this paper's own entry (BBT)
    ├── <citekey>.refs.bib    # its reference list (opencite), when a DOI exists
    └── meta.json             # provenance + hashes + timings
```

`doi-to-citekey.json` is the highest-value artifact and is cheap — one local-API scan plus one bulk
`item.citationkey` call over 1767 items. It is what lets any reference list be rewritten into the
same key namespace the drafts already use, and it should be built for the **whole library** even
during the pilot.

### `refs_export.py`

Deterministic, no LLM in the loop. Reuses what exists rather than reimplementing it:

- **Item set** — `GET /api/users/0/collections/<key>/items/top` (local API), or `--all`.
- **Citekeys** — one bulk `item.citationkey` JSON-RPC call, not one per item.
- **PDF path** — `links.attachment` from the API → `~/Zotero/storage/<attKey>/<filename>`. Same
  resolution `zotero-cli path` performs, without a subprocess per item.
- **Extraction** — `pdf_inspector.process_pdf(path)`. Carry `pdf_type`, `page_count`,
  `pages_needing_ocr`, `pages_with_tables`, `pages_with_columns` into frontmatter; they are the
  quality signal for downstream consumers and the triage list for OCR.
- **Own BibTeX** — BBT `item.export`, falling back to
  `zotero-cli export --item-keys <k> --format bibtex`.
- **Reference list** — `opencite cite <doi> --direction references -f bibtex`, skipped when no DOI.
  This is the only network step and the only slow one; Semantic Scholar rate-limits to roughly
  1 req/s, so it must be resumable and cached on disk.

Non-negotiable properties, in priority order:

1. **Read-only against Zotero.** `~/Zotero/storage/` and `zotero.sqlite` are opened for reading
   only. Never `zotero-cli add|edit|attach|delete`.
2. **Writes confined to `--out`.** Assert every output path resolves under the resolved `--out`
   root before opening it, and refuse `--out` anywhere under `~/Zotero/storage`. This is a direct
   response to the incident earlier in this repo's history, where a third-party test suite wrote to
   `$HOME` and destroyed configured API keys — see the `never-touch-home-dotfiles` and
   `sandbox-home-for-foreign-test-suites` memories.
3. **Idempotent and resumable.** Skip an item when `meta.json` records a matching source SHA-256
   *and* matching tool versions. A 1530-item run must survive interruption.
4. **Per-item failure is non-fatal.** Record the error in `index.jsonl` and continue.

### Frontmatter

```yaml
citekey: livint-popaSelectiveNeuronalVulnerability2026
zotero_key: R5STDQUE
attachment_key: HH2S76CT
doi: 10.3390/medsci14040489
title: ...
authors: [...]
year: 2026
item_type: journalArticle
collections: [...]
tags: [...]
source_sha256: ...
pages: 47
pdf_type: text_based
pages_needing_ocr: []
extractor: pdf-inspector==0.2.6
exported: 2026-09-03T00:00:00Z
```

### Pilot collection

Recommend **`Software` + `Tractography` + `Datasets`** — 42 PDFs, 1996–2025, four item types, and
7 items with no DOI, so it exercises the legacy-PDF and no-reference-graph paths. The homogeneous
alternative, `Handbook-dMR-Tractography-2025` (50 items, all `bookSection`, 100% DOI, 100% PDF),
tests only the happy path and would overstate the success rate.

## Stage 2 — citation linking (design now, build after the pilot)

The ask — "markdown with citations pointing to a bibtex" — is the hard part, and the pilot exists to
size it. Two obstacles are already measured:

- **Two citation styles coexist.** The 8-PDF sample split cleanly: some documents use numeric
  `[12]`, others author-year `(Smith et al., 2020)`. Both need handling.
- **The references heading is not always detectable.** Found in 6 of 8; a positional fallback
  (dense reference-shaped block at the tail) is required, not optional.
- **Ordering does not transfer.** `opencite cite` returns API order, unrelated to the PDF's
  numbering, so numeric styles require parsing the PDF's own reference list for order and then
  matching each parsed string to an API entry by DOI or title.

Target output is Pandoc-style `[@citekey]`, resolved through `doi-to-citekey.json` so references
already in the library get the same key the drafts use, and only genuinely-external references fall
back to opencite's key.

Ship stage 1 without inline linking. Decide on stage 2 from the pilot's measured match rate.

## Stage 3 — later, in rough order

- **Figures.** With PyMuPDF from stage 0, extract images and pair them with captions located via
  `pdf_inspector.extract_text_with_positions` (find `Figure N` items, take the nearest text block
  below). Fully local; no Mistral key needed, which is fortunate since `mistral` is unset in
  `~/.opencite/config.toml`.
- **Pin BBT citekeys** so directory names cannot drift (BBT bulk "Pin citation key"). Worth doing
  before any full run.
- **Zotero write-back**, once proven — needs a zotero.org web API key, then an Extra field or tag
  marking export state.
- **Supplementary material, code links, related DOIs** — from Zotero's `relations` and attachment
  children, which the pipeline already reads but stage 1 will not model.
- **Annotations** — `zotero-cli annotations list` per item into `annotations.md`.

## Files touched

| File | Change |
|---|---|
| `config/tools/python-tools.txt` | `zotero-mcp-server[pdf]`; add `markitdown[pdf]` |
| `config/tools/python-lock.txt` | regenerated by `--freeze` |
| `config/README.md` | correct the opencite `[pdf]` rationale; note the read-only local API |
| `plugins/refs-pipeline/**` | new plugin: 2 skills, 1 script, 1 shared reference |

`~/Zotero/derived/` is created by the script; nothing under `~/Zotero/storage/` is written.

## Verification

1. **Stage 0 repairs actually landed:**
   ```bash
   bin/rebuild-tools --check
   opencite convert "$(ls ~/Zotero/storage/*/*.pdf | head -1)" | head -20   # was: MissingDependencyException
   zotero-cli outline R5STDQUE                                              # was: PyMuPDF required
   ```
2. **Zotero is untouched by a full pilot run** — the check that matters most:
   ```bash
   md5sum ~/Zotero/zotero.sqlite > /tmp/before
   find ~/Zotero/storage -newermt '-5 minutes' | wc -l    # expect 0 after the run
   ```
   plus a run with `--out` pointed at a temp dir, confirming nothing appears in `~/Zotero/derived/`.
3. **Idempotence:** run the pilot twice. Second run reports every item skipped, and
   `find ~/Zotero/derived -newermt ...` shows only `report.md` rewritten.
4. **Extraction quality**, from `report.md`: `pages_needing_ocr` per item, references-header hit
   rate, and the citation-style split. These are the numbers that decide stage 2.
5. **Key namespace is correct:** spot-check that a citekey in `<citekey>.md` frontmatter matches
   what BBT reports for that item, and that `doi-to-citekey.json` round-trips a known DOI.
6. **Full-run cost estimate** from pilot timings: extraction seconds/item × 1530, and
   `opencite cite` calls × observed rate limit.

## Explicitly out of scope

Renaming PDFs on disk (user-driven, Zotero UI), any write to the Zotero database, obtaining a
zotero.org API key, a Mistral key, and inline citation rewriting in stage 1.

---

# Findings from a live trial — 2026-09-04

*Appended after an unplanned end-to-end trial of stage 1, performed by hand while building the
`memex` vault at `~/Projects/memex`. Two items (Hagmann 2008, Cammoun 2012) were pulled from Zotero,
converted to markdown, and ingested downstream; four more came from the network on the same task, so
the Zotero path and the opencite path were exercised side by side. Nothing was written to Zotero.*

## Corrections to the findings above

### Finding 3 is wrong: Zotero **is** writable locally

The plan states "Zotero cannot be written to. The local API is read-only … No programmatic rename,
tagging, or attaching is possible." The first clause is correct about `/api/`; that is simply not the
write path. `/connector/` is, it needs no API key, and it answers:

```
POST /connector/ping                  -> 200   supportsAttachmentUpload: true
POST /connector/getSelectedCollection -> 200   libraryEditable: true
                                               filesEditable:   true
```

This is the endpoint the browser connector uses. `zotero-cli add` sits on top of it and exposes
`doi | url | file | isbn | bibtex | csl-json`.

**No write was performed** — capability was probed, not exercised. But the following need revising:
the decisions table ("Zotero write-back: not now"), stage 3's "needs a zotero.org web API key", and
the out-of-scope list, which rules out an API key that may not be required at all.

This also answers the open question about feeding opencite output *into* Zotero: the mechanism exists
locally. `opencite pdf <doi> --convert` -> `zotero-cli add doi` for metadata -> attachment upload for
the file. See the bounded test proposed under "Still to check".

### Finding 1 refines: `opencite convert` fails only on the PDF path

Stated as "fails on every PDF". Sharper: it fails on **PDF -> markdown**, which is exactly the
`markitdown[pdf]` gap already identified. opencite's HTML/XML routes produce markdown without
touching markitdown and worked unmodified:

| paper | route | result |
|---|---|---|
| BundleCleaner, rDCM (resting-state) | HTML/XML | `.md` + `img/` — worked |
| FiberNeAT | HTML/XML | `.md` — worked |
| TAPAS | PDF | 8.5 MB `.pdf`, `MissingDependencyException` — failed |

Three of four network retrievals produced usable markdown without the broken path. Stage 0's
`markitdown[pdf]` fix is still correct; it unblocks fewer cases than "every PDF" implies. The actual
reference-list dependency, `opencite cite … -f bibtex`, was never affected.

## New findings

### `zotero-cli get fulltext` silently truncates — keep it out of the pipeline

Measured three ways on Hagmann 2008:

| source | words |
|---|---|
| `zotero-cli get fulltext` | **5,997** |
| `pdftotext` on the same PDF | 10,914 |
| Zotero's own `.zotero-ft-cache` | 10,936 |

**45% of the paper is missing and the command reports success.** The loss is against Zotero's own
index, so it is the CLI truncating, not the extraction. It is not a formatting difference:
"k-core decomposition" appears 7 times in the paper and 3 in the output, the acknowledgements are
absent, and the text stops mid-sentence — `"it must be noted that the method m"`. The output is
prefixed `*Response size: ~10K tokens. Consider using zotero_semantic_search…*`, which is the tell:
**this is an LLM-facing surface with a token budget, not a data-export surface.**

Stage 1 already calls `pdf_inspector.process_pdf` directly. That is now strongly justified rather
than merely preferred. `refs_export.py` must never shell out to `zotero-cli read` / `get fulltext`.

### `zotero-cli get children` returns 0 attachments

On three items with demonstrable PDFs, `get children` reported `count: 0` while the local API
returned them correctly. Stage 1 resolves attachment paths via `links.attachment` from the local API,
which is right; this is a second CLI surface that cannot be trusted for bulk work.

### The landing-page trap

`get fulltext` on an IEEE-sourced item returned ~22 KB and reported success. It was the Xplore
abstract page: its apparent section headings are `javascript:void(0)` links naming sections it does
not contain, and it ends in copyright boilerplate. A pipeline would emit a confident-looking
`<citekey>.md` full of publisher chrome, and every downstream consumer would treat it as the paper.

Sizing, from `~/Zotero/storage`:

| | count |
|---|---|
| storage dirs | 2,088 |
| with a PDF | 1,533 |
| HTML-only | **510** |
| with both | 0 |

Each attachment gets its own dir, so 510 HTML-only dirs is not 510 paperless items — the at-risk
population is items whose *only* text-bearing attachment is a snapshot, which by this plan's own
counts is roughly 1767 − 1530 ≈ **237 items**. Exact number still to be determined.

A working detector exists: `~/Projects/memex/_meta/validate-archive.sh`. It judges **prose volume**
(bytes on lines of >= 200 chars after paragraph unwrapping), deliberately *not* chrome position.
That distinction was arrived at by getting it wrong twice — keying on trailing chrome rejects a
complete arXiv paper carrying one line of footer nav, and treating everything after the first chrome
line as non-body rejects the Cammoun PDF, because Elsevier prints "All rights reserved" on page 1.
Chrome is a contaminant, not a verdict. It classifies all eight trial archives correctly.

### PDF page furniture is injected mid-paragraph

`pdftotext` emits running heads, feet and page numbers inline with no blank line separating them from
the body, so any paragraph-unwrapping step folds them into the text. From Hagmann 2008, verbatim:

```
and mutually interconnected. For a binary network, the k1480
```

— the page number welded onto the word "k". `~/Projects/memex/_meta/pdf-clean.sh` handles this by
learning furniture from what recurs across pages rather than hard-coding patterns (48 lines stripped
from Hagmann 2008, 111 from TAPAS), and un-welds a trailing page number only when the digits match
that page's own inferred number.

**Whether `pdf-inspector` needs this is unknown** — it returns real heading structure, so it may
already handle it. One test settles it; see below.

### Invisible C0 control bytes

`pdftotext` emits raw `0x02` / `0x03` where a superscript minus or a relational operator was:
`p , 10\x0210` is *p* < 10^-10. These are invisible in an editor, in a terminal, and in a model's
view of a file, so text that looks byte-perfect fails exact match for no visible reason. Three quotes
failed on exactly this before it was found. Fatal for any downstream provenance that relies on
grep or exact substring; merely invisible in a vector store, which is worse. Stripping C0 except
tab/newline belongs in the normalizer, at the chokepoint every document passes through.

### Duplicates are routine, and resolution must be deterministic

Hagmann 2008 appears twice (PMC capture carrying the DOI; Google Scholar capture without one).
BundleCleaner appears twice under a single bioRxiv DOI, as a Crossref `report` and a PMC
`journalArticle` with identical attached text. `doi-to-citekey.json` needs an explicit tiebreak —
suggested: **attachment passes validation, then richest metadata** — or it silently resolves by scan
order and the winner changes between runs.

### `.zotero-ft-cache` may be a zero-cost extraction source

**1,479 of 1,533 PDF dirs (96.5%) already carry a `.zotero-ft-cache`**, 135 MB in total, and the
Hagmann sample matches `pdftotext` almost exactly (10,936 words vs 10,914). It is flat text — no
headings, no tables, and it carries the same page furniture and C0 bytes — so it is not a substitute
for `pdf-inspector` where structure matters. But it is already on disk and free, which makes it a
credible fast path, a cross-check against extraction drift, or a stopgap for the 54 dirs that lack
one. Worth measuring before committing to a full extraction run.

## Reusable components

Three deterministic, idempotent, dependency-free bash scripts written during the trial, all in
`~/Projects/memex/_meta/`, all with their rationale in the file header:

| script | does |
|---|---|
| `normalize.sh` | folds ligatures/quotes/dashes, rejoins hyphenated line breaks, unwraps paragraphs to one line, strips C0 controls |
| `pdf-clean.sh` | strips learned page furniture and un-welds page numbers; run before `normalize.sh` |
| `validate-archive.sh` | rejects landing pages on prose volume; exit 0/1 |

## Suggested changes to the stages

- **Rewrite finding 3**, and move connector-based write-back out of stage 3 into a scoped stage 2.5,
  gated on the round-trip test below.
- **Add a validation gate** between extraction and write in `refs_export.py`, recording the verdict
  in frontmatter as `text_quality: validated | metadata_only | rejected` rather than refusing to
  export. Downstream consumers can then filter; a silent bad export cannot be filtered at all.
- **Add a normalization stage** before markdown is written: strip C0 controls, strip page furniture.
- **Add to `report.md`**: count rejected as landing pages, and C0-byte incidence. Both are one-line
  greps, and both are what tell you whether the tree is trustworthy.
- **Pilot collection**: the proposed `Software` + `Tractography` + `Datasets` still looks right.
  Add at least one deliberately HTML-only item so the pilot exercises the trap rather than
  discovering it at full-run scale.

## Still to check

Ordered by how much the answer would change the design.

1. **Does the connector write path actually work end-to-end?** Capability was advertised, not
   exercised. Bounded test: one DOI not currently in the library, into a throwaway collection,
   `md5sum ~/Zotero/zotero.sqlite` before and after, item deleted afterwards. Confirm whether
   metadata-add and attachment-upload are separately available, and whether an item created this
   way gets a BBT citekey immediately or only after a sync.
2. **Does `pdf-inspector` strip page furniture, and does it emit C0 bytes?** Run it on
   `~/Zotero/storage/W3FKDHLX/*.pdf` (Hagmann 2008) and grep for `PLoS Biology | www.plosbiology.org`
   and for `[\x01-\x08\x0b\x0c\x0e-\x1f]`. If clean, `pdf-clean.sh` is unnecessary in this
   pipeline and the C0 strip can be dropped too. If not, both belong in stage 1.
3. **Does `zotero-cli read` truncate the way `get fulltext` does?** `read` is pdf-inspector-backed
   and the plan cites it as evidence the extractor works. If it shares the token cap, the benchmark
   table in "What the probe established" was measured through a capped surface and the character
   counts understate the real output.
4. **Exact count of items with no PDF attachment**, and of items whose only attachment is an HTML
   snapshot. Estimated at ~237 above from top-level counts; the real number sets the size of the
   landing-page problem and belongs in `report.md`.
5. **Is BBT JSON-RPC still live?** Asserted in the original probe, not re-verified on 2026-09-04.
   `item.citationkey` in bulk is load-bearing for the whole export tree.
6. **Rate limiting is real and needs explicit backoff.** This session hit `HTTP 429` from bioRxiv on
   first attempt (succeeded on retry) and Semantic Scholar returned a 500 and a rate-limit warning
   through opencite. The plan's resumability requirement is confirmed necessary; add explicit
   retry-with-backoff rather than relying on opencite's internal handling, and cache negative
   results so a re-run does not re-hit a failing DOI.
7. **Pin BBT citekeys before any full run.** Already noted in stage 3, but it is a precondition for
   the export tree, not a later nicety: unpinned keys mean directory names can drift and a re-run
   silently produces a second tree rather than updating the first.
8. **Does `opencite cite --direction references` cover the library as assumed?** 86% DOI coverage is
   from the original probe; worth confirming the *reference-list* hit rate on the pilot, since a DOI
   existing does not mean the reference graph is populated for it.
9. **Sanity-check one export end to end against a known-good result.** Hagmann 2008 and Cammoun 2012
   were extracted by hand this session and are archived under `~/Projects/memex/.archive/`. They are
   a ready regression fixture for whatever the pipeline produces.
