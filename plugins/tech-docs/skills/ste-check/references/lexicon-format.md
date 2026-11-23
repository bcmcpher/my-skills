# Common lexicon format

A lexicon is a JSON file that lists words and says which ones to use. The checker
(`ste_check.py`) reads only this format. It knows nothing about STE, PDFs or any other source.
The builder (`lexicon.py`) converts a source dictionary into this format.

## Top level

| Field | Type | Meaning |
|---|---|---|
| `name` | string | A label for reports, for example `ste100-issue9`. |
| `closed` | boolean | `true` when the approved entries are a complete vocabulary. |
| `entries` | array | One object per term and part of speech. |

A closed lexicon enables the `jargon` flag, because only then does "not in the list" mean
something. ASD-STE100 is closed. A replacement list, such as a personal list of words to avoid, is
open.

## Entries

| Field | Type | Required | Meaning |
|---|---|---|---|
| `term` | string | yes | One word or a phrase. Matched without regard to case. |
| `approved` | boolean | yes | `true` if the term is approved. |
| `pos` | string | no | Part of speech: `n`, `v`, `adj`, `adv`, `pron`, `art`, `prep` or `conj`. |
| `kind` | string | no | `TN` (technical noun) or `TV` (technical verb). Marks a declared technical term. |
| `forms` | array of strings | no | The permitted inflections of an approved term, for example `["adapts", "adapted"]`. |
| `alternatives` | array of objects | no | For a term that is not approved: the approved terms to use instead. |

Each alternative has a `term`, and an optional `pos` and `kind`. Only an entry with
`approved: false` can have alternatives.

The same term can have more than one entry, one for each part of speech. The checker has no
part-of-speech tagger, so it treats a term as approved when any of its entries is approved.

`forms` matters only for an approved term in a closed lexicon. When an approved entry lists its
forms, the checker accepts only those forms. When it lists none, the checker accepts the plain
plural (`-s`, `-es`).

## Stacking

The checker takes `--lexicon` more than once. A later lexicon overrides an earlier one for the
same term: all entries for that term come from the later lexicon. The `jargon` flag is on when at
least one loaded lexicon is closed.

## Declared technical terms

A project's declared terms become one more open lexicon, loaded last. Each declared term is an
approved entry with `kind` `TN` or `TV`. The sources are a `.tech-terms` file at the project root
(or `--terms <file>`) and the project glossary. See the `ste-check` skill for the file syntax.

## Example

```json
{
  "name": "plain-words",
  "closed": false,
  "entries": [
    {"term": "utilize", "pos": "v", "approved": false,
     "alternatives": [{"term": "use", "pos": "v"}]},
    {"term": "use", "pos": "v", "approved": true, "forms": ["uses", "used"]},
    {"term": "codegraph", "approved": true, "kind": "TN"}
  ]
}
```

## Where lexicons live

The builder writes to `${XDG_DATA_HOME:-~/.local/share}/tech-docs/lexicons/<name>.json`. It
refuses any output path inside a git work tree, so a lexicon derived from a licensed dictionary
cannot be committed by mistake.
