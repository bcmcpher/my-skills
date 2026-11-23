# tech-docs

Write and check technical documentation in ASD-STE100 Simplified Technical English (STE), applied
at about 80%. The plugin has one agent and two skills:

| Part | Kind | What it does |
|---|---|---|
| `technical-docs-writer` | agent | Writes or revises a doc, checks it, and fixes the flagged sentences. |
| `/ste-check` | skill | Scores docs against STE rules and lists jargon leaks and spelling variants. |
| `/doc-quadrants` | skill | Labels each section as tutorial, how-to guide, reference or explanation. |

The aim is consistent terms and phrasing, and no unplanned jargon. Full STE compliance is not
the aim.

## Install

1. Add this repository as a marketplace, once, from the repository root:
   `claude plugin marketplace add .`
2. Install the plugin: `claude plugin install tech-docs@local`.

The scripts need Python 3.10 or later and only the standard library. The STE lexicon builder also
needs `pdftotext` from poppler-utils.

## Build a lexicon

A lexicon is a JSON word list in a common format (see
[`lexicon-format.md`](skills/ste-check/references/lexicon-format.md)). The checker reads only
this format, so any dictionary can feed it.

- From an ASD-STE100 Issue 9 PDF that you hold a license for:

  ```bash
  python3 -I skills/ste-check/scripts/lexicon.py build --from ste-pdf ~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf
  ```

  The build checks the entry counts (879 approved, 1317 not approved). It writes nothing if
  they differ.
- From a plain word list, one `term<TAB>replacement[<TAB>pos]` per line:

  ```bash
  python3 -I skills/ste-check/scripts/lexicon.py build --from tsv my-words.tsv
  ```

Lexicons go to `~/.local/share/tech-docs/lexicons/`. The builder refuses a path inside a git
work tree, so a lexicon from a licensed dictionary cannot reach a repository.

## Check docs

```bash
python3 -I skills/ste-check/scripts/ste_check.py --lexicon ste100-issue9 --show 10 README.md docs/
```

The score is the share of sentences with no flags. The target is about 80%. The checker exits 0
on findings: it is a soft audit, not a gate. It exits 2 on a bad lexicon or a missing path.

| Flag | Meaning |
|---|---|
| `length`, `passive`, `ing`, `hedge`, `multi-instruction` | Sentence rules |
| `word` | A term that is not approved, with its approved alternatives |
| `form` | An inflection that the lexicon does not list for an approved term |
| `jargon` | A word in no loaded lexicon and not declared (closed lexicons only; not scored) |
| `variant` | One term written two ways in the doc set |

Without a closed lexicon, such as on CI, `jargon` is off and the report says so.

## Declare technical terms

A project declares its technical terms in `.tech-terms` at its root. Each line holds one term in
its canonical spelling. A tab and `TV` marks a technical verb. The checker also reads the defined
terms in `GLOSSARY.md`, `docs/glossary.md`, or a "Key terms" section.

Declared terms are accepted, and they set the correct spelling for `variant`. Write the list from
the code and the manifests, not from the docs under check. A list built from the docs hides the
leaks that it should show.

## Terms

- **Lexicon:** a word list in the common format. A *closed* lexicon is a complete vocabulary, so
  a word outside it is a leak.
- **Declared term:** a technical noun or verb that a project permits, from `.tech-terms` or the
  glossary.
- **Leak:** a word in no loaded lexicon and not declared.
- **Variant:** one term written two ways, such as `code graph` and `codegraph`.

## Tests

The tests use synthetic fixtures only. Run them from the repository root:

```bash
uv run --python 3.12 --with pytest pytest plugins/tech-docs/tests
```

## Sources

- ASD-STE100 Simplified Technical English, Issue 9. The dictionary is ASD's copyright. This
  plugin reads it from your own PDF and stores no part of it.
- The quadrant model: Daniele Procida's [Diátaxis](https://diataxis.fr/), as summarized by
  [Steve Dunn](https://dunnhq.com/posts/2023/documentation-quadrants/).
