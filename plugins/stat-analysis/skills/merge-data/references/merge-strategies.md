# Merge Strategies

Reference for join types, key-name heuristics, wide/long format detection,
duplicate handling, and post-merge validation. Used by merge-data and merge-agent.

---

## Key-name heuristics

A column is likely a merge key (index/identifier) if its name matches one of these
patterns (case-insensitive, after stripping underscores, hyphens, and spaces):

| Pattern group | Example column names | Likely meaning |
|---|---|---|
| `sub`, `subject`, `subjectid`, `participant`, `participantid` | `sub`, `subject_id`, `participant_id` | Subject / participant identifier |
| `ses`, `session`, `sessionid`, `visit`, `visitnum`, `timepoint` | `ses`, `session_id`, `visit_num` | Session or longitudinal timepoint |
| `run`, `runid`, `runnum`, `runnumber` | `run`, `run_id`, `run_number` | Within-session run repetition |
| `task`, `taskname`, `condition` (when used as index) | `task`, `task_name` | Task condition label (BIDS) |
| `id`, `uid`, `caseid`, `recordid`, `pid` | `id`, `case_id`, `record_id` | Generic row identifier |
| `date`, `scandate`, `acqdate`, `acquisitiondate` | `date`, `scan_date` | Acquisition date — use cautiously as a key |
| `site`, `siteid`, `scanner`, `center`, `centerid` | `site_id`, `scanner` | Multi-site data; sometimes part of a composite key |

Columns that are likely **categorical variables, not keys**, even if they have
identifier-like names: `group`, `arm`, `cohort`, `diagnosis`, `sex`, `gender`.
These typically have cardinality ≤ 20. Verify intent with the user before using
them as join keys.

Key columns typically have:
- Low or zero null fraction across all files
- Cardinality close to the number of rows in each file (for subject-level keys)
- Consistent value format across files (same prefix style, same zero-padding)

---

## BIDS subject/session ID conventions

BIDS encodes identifiers as entity-value pairs in filenames: `sub-01`, `ses-baseline`.
Participant tables (`participants.tsv`) store the bare label (`01`) in a
`participant_id` column — the `sub-` prefix is **not** included in the TSV.

When merging BIDS-adjacent data:

1. Check whether each file uses prefixed (`sub-01`) or bare (`01`) IDs.
2. If mixed, normalize to bare labels (strip the `sub-` or `ses-` prefix) and
   document the normalization step as a comment in the generated script.
3. Session labels in BIDS are alphanumeric strings (`ses-01`, `ses-baseline`), not
   plain integers. Normalize consistently across files — don't mix `"01"` and `1`.
4. Zero-padding matters: `sub-01` ≠ `sub-1`. Standardize padding before joining.

---

## Join types

| Join | Rows in output | When to use |
|---|---|---|
| **inner** | Only rows with a matching key in **every** file | All subjects appear in every file; no missing data is expected |
| **left** | All rows from the leftmost (base) file; NaN fill for non-matches | One master participant list; other files may have incomplete coverage |
| **right** | All rows from the rightmost file; NaN fill for non-matches | Rarely the right choice for multi-file merges; prefer left |
| **outer (full)** | All rows from any file; NaN fill for all non-matches | Maximum data retention; produces the most NaN columns |

**Default recommendation:** left join on a master participant list (demographics TSV
or subject manifest). This preserves all subjects and makes gaps in secondary files
immediately visible in the output.

**When inner is safe:** Only when the user confirms that all files contain exactly
the same set of subjects. Verify by comparing the full key column sets before
committing — never assume they match just because row counts are similar.

**What inner join silently loses:** Any subject present in the base file but absent
from a secondary file is dropped without warning. Always compute and print
`len(base) - len(merged)` rows dropped, so the user can see the cost.

---

## Detecting file structure: subject-split vs. multi-variable

These are the two most common structures in research data folders.

### Case A — Multi-variable (join horizontally)

Multiple files, each covering different measurement domains, sharing an index column.

Evidence:
- File names reflect different data types: `demographics.csv`, `neuropsych.csv`, `imaging_summary.csv`
- Each file has mostly different column names (except the shared key)
- Row counts are similar across files (roughly one row per subject)
- A common key column (subject ID ± session) is present in most or all files

Action: join files on the shared key column(s).

### Case B — Subject-split (stack vertically first)

One file per subject (or per subject × session), all with the same column layout.

Evidence:
- File names follow a repeating pattern: `sub-01_measures.csv`, `sub-02_measures.csv`
- Column headers are identical (or nearly identical) across all files
- Row count per file is small (often 1 row per file, or one row per timepoint)
- The subject identity is encoded in the filename, not in a column

Action: stack with `pd.concat`, then optionally join to a wide demographics file.

### Mixed case (stack → join)

Subject-split files that also need to be joined to a wide summary file.
1. Stack the subject-split files into a single dataframe.
2. Join the stacked result to the wide file on the shared key.
3. Generate separate load functions for the two structures in the script.

**Do not assume subject-split structure based on file count alone.** A folder with
20 files could be 20 different measurement types, not 20 subjects. Look for the
filename pattern and identical column sets before deciding.

---

## Wide vs. long format

**Wide format:** One row per subject (or subject × session); one column per variable.
- Typical for demographics tables, neuropsych battery scores, imaging summaries.
- Required by most statistical models in R and Python.

**Long format:** One row per subject × variable combination, with a `variable` column
naming each measurement.
- Typical for repeated-measures data, time-series, or feature matrices.
- Required by `ggplot2` and `seaborn` for faceted plots.

**Detecting long format:**
- Presence of a column named `variable`, `measure`, `metric`, `feature`, `column_name`
- Only 1–3 numeric columns alongside several categorical index columns
- Row count is much greater than the number of subjects

**When to reshape:**
- If all inputs are wide and the user needs long format, add a `melt()` /
  `pivot_longer()` call after the merge.
- If inputs are mixed wide and long, merge on the wide side first, then melt.
  Do not join a wide file to a long file directly without pivoting one of them first.

```python
# Wide → long (Python / pandas)
long_df = df.melt(
    id_vars=["subject_id", "session"],
    value_vars=[c for c in df.columns if c not in ["subject_id", "session"]],
    var_name="variable",
    value_name="value",
)

# Long → wide (Python / pandas)
wide_df = long_df.pivot_table(
    index=["subject_id", "session"],
    columns="variable",
    values="value",
).reset_index()
wide_df.columns.name = None   # remove the column axis name artifact
```

```r
# Wide → long (R / tidyr)
library(tidyr)
long_df <- pivot_longer(df, cols = -c(subject_id, session),
                        names_to = "variable", values_to = "value")

# Long → wide (R / tidyr)
wide_df <- pivot_wider(long_df, names_from = "variable", values_from = "value")
```

---

## Handling duplicates

### Duplicate rows (identical key + identical values)

Drop with `df.drop_duplicates()` and log the count removed. Never drop silently.

### Duplicate keys with different values (conflicting records)

This is a data quality problem, not a merge artifact. Do not drop rows. Instead:
1. Report which key values have duplicate entries and how many.
2. Show which columns differ between the duplicates.
3. Ask the user how to resolve before proceeding.

Resolution options to offer: keep first, keep last, compute mean/max/mode, flag
the ambiguous rows with a new `_conflict` boolean column.

### Column name conflicts after merge

- If two files share a non-key column name with **identical values** (verified by
  sampling), keep one copy and drop the other.
- If two files share a non-key column name with **different values**, keep both with
  informative suffixes: use the source file's stem as the suffix (e.g.,
  `score_neuropsych`, `score_imaging`), never the pandas default `_x` / `_y`.

---

## Composite keys

Some datasets require two or more columns to uniquely identify a row (e.g.,
`subject_id + session`, or `subject_id + site`).

Signs that a single-column key is insufficient:
- The presumed key column has duplicates within a single file
- A join on one column produces more rows than expected (many-to-many explosion)
- Both subject and session columns are present in the same file

Always verify uniqueness before joining:

```python
# Python — assert composite key is unique within each file
assert not df.duplicated(subset=["subject_id", "session"]).any(), (
    f"Duplicate subject×session combinations: "
    f"{df[df.duplicated(subset=['subject_id','session'])][['subject_id','session']].to_dict('records')}"
)
```

```r
# R — check for duplicate composite keys
stopifnot(!any(duplicated(df[c("subject_id", "session")])))
```

---

## Post-merge validation checklist

After every merge, compute and log all of the following:

1. **Shape**: Expected row count matches intent.
   - Inner join: should be ≤ min(file row counts)
   - Left join: should equal the row count of the base (left) file
   - Outer join: should be ≥ max(file row counts)
   - Subject-split stack: should equal the sum of all stacked file row counts

2. **Missing values by column**: Print columns with > 0 missing, sorted descending.
   Any column with > 10% missing after a join likely signals a key mismatch or
   format inconsistency — flag for the user to review.

3. **Key coverage per source file**: For each file joined, compute what fraction of
   its rows matched a key in the base file.
   - 100% match → key alignment confirmed
   - < 80% match → strong signal of a format or prefix mismatch; investigate before
     delivering output

4. **Duplicate rows in output**: `df.duplicated().sum()` should be 0. A non-zero
   count indicates a many-to-many join caused by a non-unique key in one of the files.

5. **Column count sanity**: Total columns should be approximately
   `sum(unique columns per file) - (n_files - 1) × n_shared_key_columns`.
   An unexpectedly large column count suggests a many-to-many join or a column
   suffix explosion.

Print all of the above as a validation block at the end of `build_merged()`. This
block runs every time the script is executed and makes join problems immediately
visible.
