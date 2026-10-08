# STE-based writing style: checker and A/B harness

**Date:** 2026-10-08
**Decision:** keep `writing.md`. It moved the score from 79% to 97% with no overlap between arms,
and the shorter READMEs kept the same facts.
**Plan:** [`plans/global-claude-md-defaults.md`](../../plans/global-claude-md-defaults.md)

## Question

Does `config/writing.md` make the documentation Claude writes measurably closer to ASD-STE100?
And can compliance be tested at all without the licensed STE dictionary?

## The checker

`ste_check.py` is stdlib-only Python. It scores Markdown against the STE rules that can be
measured:

| Rule | Flag |
|---|---|
| Procedural sentence ≤20 words, descriptive ≤25 | `length` |
| Active voice | `passive` (form of *be*/*get* + past participle) |
| No -ing forms except technical names | `ing` |
| Approved words — a short list of common violations, **not** the dictionary | `word` |
| No hedging | `hedge` |
| One instruction per sentence | `multi-instruction` |
| Paragraphs ≤6 sentences | reported per file |

Score = percentage of sentences with no flags. Code, tables, headings and link targets are
stripped first. A sentence is procedural if it is a numbered-list item or starts with an
imperative verb. `--ignore <rule>` drops a rule; `--show N` prints the worst sentences.

```bash
python3 -I evaluations/2026-10-08-ste-docs/ste_check.py --show 10 README.md
```

## Calibration (existing docs, written without the style)

| Doc | All rules | Without `ing` |
|---|---|---|
| `config/README.md` | 56.8% | 68.8% |
| `plugins/datalad-cli/README.md` | 61.5% | — |
| `plugins/stat-analysis/README.md` | 53.8% | — |
| `plugins/bids/README.md` | 71.9% | 87.5% |
| `evaluations/2026-09-14-code-graph-tools/README.md` | 75.3% | — |
| `crane/README.md` | 73.8% | 85.2% |
| `config/writing.md` (the style file itself) | 82.6% | — |

Spot checks of flagged sentences found mostly true positives. The `ing` rule is the noisiest,
because STE allows -ing in technical names ("operating system"), and the checker cannot tell.
At "80% application", `--ignore ing` is a reasonable reading. Current docs then score 69–88%.

## A/B result

`run.sh 3 boutiques`, run on 2026-10-08 with Claude Code `--model opus`. Each run had read-only
tools. The prompt was the same in both arms: write a README for `plugins/boutiques/`. Both arms
loaded the live global config and the project CLAUDE.md. Only the `ste` arm also had
`config/writing.md` appended to its system prompt. Outputs are in `runs/` (gitignored).

| Arm | Run | Score | Without `ing` | Sentences | Words |
|---|---|---:|---:|---:|---:|
| base | 1 | 78.8% | 86.5% | 52 | 874 |
| base | 2 | 77.8% | 86.7% | 45 | 780 |
| base | 3 | 80.0% | 87.5% | 40 | 785 |
| ste | 1 | 96.1% | 96.1% | 51 | 651 |
| ste | 2 | 95.9% | 100.0% | 49 | 663 |
| ste | 3 | 97.6% | 97.6% | 42 | 526 |

- **The effect is large and consistent.** The means are 78.9% and 96.5%, and the arms do not
  overlap. Run-to-run spread is about 2 points.
- **Passive voice and -ing forms went down the most.** Across the three runs, the `base` arm had
  10 passive and 14 -ing flags, and the `ste` arm had 1 and 2.
- **The `ste` READMEs are about 25% shorter** (613 vs 813 mean words), with fewer examples.
  Spot checks of the key facts found the same coverage in both arms: schema 0.5, `bosh`,
  validation, limits and `--help` parsing. One `base` run named CBRAIN, and no `ste` run did.
  Every license mention came from `plugin.json`.
- **Limits of the test:** one plugin, n=3, and one judge, which is the heuristic checker. Nothing
  here measures whether a reader finds the shorter README more useful.

## Rerun

Run it in tmux, because it takes several minutes and makes 2N billed calls:

```bash
cd evaluations/2026-10-08-ste-docs
tmux new-session -d -s ste-ab 'env -u CLAUDECODE ./run.sh 3 boutiques 2>&1 | tee logs/ab.log'
```

`run.sh` refuses to run once `writing.md` is imported by `~/.claude/CLAUDE.md`. After that,
compare against a run with the import commented out.

## Later

If the checker proves useful, port its rules to [Vale](https://vale.sh). Look for an existing
community STE package first.
