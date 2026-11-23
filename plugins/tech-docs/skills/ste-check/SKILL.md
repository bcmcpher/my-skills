---
name: ste-check
description: Score Markdown documentation against ASD-STE100 Simplified Technical English rules and find jargon leaks — sentence length, passive voice, -ing forms, hedges, non-approved words with their approved alternatives, unlisted inflections, undeclared technical terms and inconsistent spellings — with a deterministic checker that reads any dictionary in a common lexicon format. Also builds that lexicon from a local ASD-STE100 PDF or a plain word list. Use when asked to check docs against STE or a word list, find jargon or undeclared terms, check term spelling consistency, build a lexicon, or write a .tech-terms file.
argument-hint: [files or directories] [--lexicon name]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Skill: ste-check

Check documentation with `ste_check.py`, and build lexicons for it with `lexicon.py`.
`<scripts>` is `${CLAUDE_PLUGIN_ROOT}/skills/ste-check/scripts`.
`<refs>` is `${CLAUDE_PLUGIN_ROOT}/skills/ste-check/references`.
Both scripts are stdlib-only Python. Run them with `python3 -I`.

The checker is a soft audit. It always exits 0 on findings, and it never blocks. The score
target is about 80%, the `writing.md` level, not 100%.

## Steps

1. **Find the lexicons.** List `${XDG_DATA_HOME:-~/.local/share}/tech-docs/lexicons/`. A lexicon
   loads by name (`--lexicon ste100-issue9`) or by path.
2. **Build a lexicon if one is missing.** Use one of these commands:
   - STE: `python3 -I <scripts>/lexicon.py build --from ste-pdf [<pdf>]`. The PDF defaults to
     `$STE100_PDF`, else `~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf`. The build checks the
     Issue 9 counts (879 approved, 1317 not approved) and writes nothing if they differ.
   - Any word list: `python3 -I <scripts>/lexicon.py build --from tsv <file>`. Each line is
     `term<TAB>replacement[<TAB>pos]`. An empty replacement marks an approved term.
   The format is in `<refs>/lexicon-format.md`. Never write a lexicon into a repository; the
   builder refuses a path inside a git work tree.
3. **Check for declared terms.** Look for `.tech-terms` at the project root and for a glossary
   (`GLOSSARY.md`, `docs/glossary.md`, or a "Key terms" section). If none exists and the user
   wants jargon findings, offer to write `.tech-terms` (step 6).
4. **Run the checker.** Use this command:
   `python3 -I <scripts>/ste_check.py --lexicon ste100-issue9 --show 10 <files or dirs>`.
   Stack lexicons by repeating `--lexicon`; a later one overrides an earlier one. Use `--terms
   <file>` for a terms file elsewhere, `--jargon` for the leak list only, `--json` for
   machine-readable output, and `--ignore <rule,...>` to skip rules.
5. **Read the report.** Explain each kind of finding in plain terms:
   - `length`, `passive`, `ing`, `hedge`, `multi-instruction`: sentence rules.
   - `word`: a term that is not approved, with its approved alternatives.
   - `form`: an inflection of an approved term that the lexicon does not list.
   - `jargon`: a word in no loaded lexicon and not declared. It does not lower the score.
   - `variant`: one term written two ways, or a non-approved term next to its alternative.
   - The suppression lines show how many hits each declared-term source hid. A source that hides
     a large share of all hits is too broad.
6. **Triage jargon leaks.** For each leak, recommend one action: declare it, define it in the
   glossary, or rewrite it. A frequent leak probably needs declaring. A leak used once is the
   likeliest unplanned term. Propose `.tech-terms` additions as a list for the user to approve.

## The `.tech-terms` file

One term per line, in its canonical spelling. Add `<TAB>TV` for a technical verb; `TN` is the
default. `#` at the start of a line, or after a space, starts a comment.

```
# product names, tools, file formats, domain nouns
CodeGraph
pyproject.toml
lexicon
validate	TV
```

Write the list from the source material — code, `plugin.json`, the domain — never from the docs
that the checker scores. A list built from the output makes the leak count circular.

## Constraints

- No dictionary text, lexicon file or extract goes into a repository.
- Without a closed lexicon, `jargon` is off and the report says so. That is expected on CI.
- The checker has no part-of-speech tagger. It treats a term as approved when any of its entries
  is approved, and it treats a word after a determiner as a noun. Expect some false `word` hits.
- Do not edit the user's `.tech-terms` or glossary to silence findings. Propose the change.
