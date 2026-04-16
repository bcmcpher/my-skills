# Data Quality Checks

Reference for pre-merge and post-load data quality inspection. Covers five
systematic check patterns and language-specific tooling. Used by merge-data
(Phase 1 inspection), gen-data-dict, and any skill that needs to validate
field content before analysis.

---

## 1. Column profiling — get a full picture before doing anything else

Run a column profile on every file before deciding on merge keys or join strategy.
A good profile surfaces null rates, type inconsistencies, cardinality, and
distribution shape in one pass — which is cheaper than discovering problems after
generating code.

**What to report per column:**
- Dtype as stored
- Non-null count and null fraction
- Cardinality (unique value count and ratio to total rows)
- Sample values (5 representative values, including any unusual ones)
- For numerics: min, median, max, and whether the distribution looks plausible
- For categoricals: top-5 levels by frequency and any rare/singleton values
- For strings: any obvious structural patterns (dates, IDs, free text)

### Python — skrub TableReport (recommended for interactive inspection)

```python
from skrub import TableReport, column_associations
import pandas as pd

df = pd.read_csv("data.csv")

# Interactive HTML report: column stats, distributions, and association heatmap
report = TableReport(df)
report.open()                    # opens in browser
report.write_html("profile.html")  # save for sharing

# Pairwise statistical associations between all column pairs
assoc = column_associations(df)  # returns DataFrame of association measures
```

`TableReport` shows four tabs: a row sample, per-column statistics (null rate,
unique count, dtype), distribution plots, and a column-association heatmap. It
works with both pandas and polars DataFrames.

### Python — pandas quick profile (no extra dependencies)

```python
import pandas as pd

def profile_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Compact column profile: dtype, null rate, cardinality, samples."""
    rows = []
    for col in df.columns:
        s = df[col]
        n_null = s.isna().sum()
        n_unique = s.nunique(dropna=True)
        samples = s.dropna().unique()[:5].tolist()
        rows.append({
            "column":      col,
            "dtype":       str(s.dtype),
            "n_rows":      len(s),
            "n_null":      n_null,
            "null_pct":    round(100 * n_null / len(s), 1),
            "n_unique":    n_unique,
            "unique_ratio": round(n_unique / max(len(s) - n_null, 1), 3),
            "samples":     samples,
        })
    return pd.DataFrame(rows)

profile = profile_dataframe(df)
print(profile.to_string(index=False))
```

### R — skimr (recommended)

```r
library(skimr)
library(dplyr)

# Rich summary: type, missing, complete rate, quartiles, histogram
skim(df)

# Per-column missingness heatmap (visual, requires naniar)
library(naniar)
vis_miss(df)                     # heatmap of missing values
gg_miss_var(df)                  # bar chart of missingness by column
```

### Julia — DataFrames describe

```julia
using DataFrames, Statistics

# Built-in column summary
describe(df)   # dtype, nmissing, nnonmissing, eltype, min, median, max

# Custom null profile
function profile_df(df::DataFrame)
    n = nrow(df)
    [(col=c,
      dtype=eltype(df[!, c]),
      n_missing=count(ismissing, df[!, c]),
      null_pct=round(100 * count(ismissing, df[!, c]) / n, digits=1),
      n_unique=length(unique(skipmissing(df[!, c]))))
     for c in names(df)]
end
profile_df(df)
```

---

## 2. Missing data analysis

**Why it matters for merges:** A column that looks like a good key may have hidden
missing values represented as blank strings, coded strings ("NA", "N/A", ".", " "),
or numeric sentinels (−9, −99, 9999). These will produce phantom key mismatches.

**Normalize missing-value representations at load time:**

```python
# Python — extend the default NA list before reading
EXTRA_NA = ["", " ", "N/A", "n/a", "NA", "na", "NaN",
            "nan", "None", "none", ".", "..", "Unknown",
            "unknown", "UNKNOWN", "-9", "-99", "9999"]

df = pd.read_csv("file.csv", na_values=EXTRA_NA, keep_default_na=True)

# Verify: print columns with any residual suspicious string values
str_cols = df.select_dtypes("object").columns
for col in str_cols:
    suspicious = df[col].str.strip().isin(EXTRA_NA).sum()
    if suspicious:
        print(f"  {col}: {suspicious} suspicious strings still present")
```

```r
# R — readr treats these as NA automatically; extend with na argument
library(readr)
extra_na <- c("", " ", "N/A", "n/a", "NA", "na", ".", "..",
              "Unknown", "unknown", "-9", "-99", "9999")
df <- read_csv("file.csv", na = extra_na)

# Check missingness by column
library(dplyr)
df |> summarise(across(everything(), ~sum(is.na(.))))
```

```julia
# Julia — CSV.jl missingstring option
using CSV, DataFrames
df = CSV.read("file.csv", DataFrame;
              missingstring=["", "N/A", "NA", ".", "Unknown", "-9", "-99", "9999"])

# Count missing per column
map(c -> (col=c, n_missing=count(ismissing, df[!, c])), names(df))
```

**Missingness pattern analysis — are gaps correlated?**

When two columns are both missing for the same rows, it signals a structural
cause (e.g., a whole visit was skipped). Always check before a merge.

```python
# Python — missingness correlation
import pandas as pd
miss_matrix = df.isna().astype(int)
if miss_matrix.sum().sum() > 0:
    # Columns that are missing together more than expected by chance
    print(miss_matrix.corr().round(2))
```

```r
# R — naniar provides a tidy missingness upset plot
library(naniar)
gg_miss_upset(df, nsets = 10)   # shows co-occurrence of missing values
```

---

## 3. Type validation

**Why it matters:** A column that should be numeric but contains strings ("12.5 mg")
will not merge cleanly on a numeric key and will silently become NaN. A date stored
as a string in two different formats ("2021-01-15" vs "15/01/2021") will fail a join.

**Validate expected types before merging:**

```python
# Python — detect numeric columns stored as strings
import pandas as pd, re

def find_numeric_strings(df: pd.DataFrame) -> list[str]:
    """Identify object columns whose non-null values are all numeric-looking."""
    suspect = []
    for col in df.select_dtypes("object").columns:
        sample = df[col].dropna().head(50)
        if sample.str.match(r"^-?\d+(\.\d+)?$").all():
            suspect.append(col)
    return suspect

print("Numeric strings:", find_numeric_strings(df))

# Detect date strings in various formats
def find_date_strings(df: pd.DataFrame) -> list[str]:
    date_pat = re.compile(
        r"\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}\.\d{2}\.\d{4}"
    )
    return [c for c in df.select_dtypes("object").columns
            if df[c].dropna().head(20).str.match(date_pat).mean() > 0.8]

print("Date strings:", find_date_strings(df))
```

```r
# R — check for numeric-looking character columns
library(dplyr)
df |>
  select(where(is.character)) |>
  summarise(across(everything(),
    ~mean(!is.na(suppressWarnings(as.numeric(.)))))) |>
  pivot_longer(everything(), names_to="column", values_to="numeric_fraction") |>
  filter(numeric_fraction > 0.9)   # mostly parseable as numeric
```

**Schema validation — expected types defined upfront:**

```python
# Python — lightweight schema check without extra dependencies
EXPECTED_TYPES = {
    "subject_id": "object",      # string identifier
    "age":        "float64",
    "diagnosis":  "category",
    "scan_date":  "datetime64[ns]",
}

for col, expected in EXPECTED_TYPES.items():
    if col not in df.columns:
        print(f"MISSING: {col}")
    elif str(df[col].dtype) != expected:
        print(f"TYPE MISMATCH: {col} — expected {expected}, got {df[col].dtype}")
```

---

## 4. Duplicate detection

### Exact duplicates (identical rows)

Always check before stacking subject-split files — two exports of the same session
will produce silent double-counting.

```python
# Python
n_exact = df.duplicated().sum()
if n_exact:
    print(f"WARNING: {n_exact} exact duplicate rows")
    df = df.drop_duplicates()
    print(f"  → Dropped. Remaining rows: {len(df)}")
```

```r
# R
n_exact <- sum(duplicated(df))
if (n_exact > 0) {
  message(sprintf("WARNING: %d exact duplicate rows", n_exact))
  df <- df[!duplicated(df), ]
}
```

```julia
# Julia
n_exact = nrow(df) - nrow(unique(df))
if n_exact > 0
    println("WARNING: $n_exact exact duplicate rows")
    df = unique(df)
end
```

### Near-duplicate and fuzzy categorical values

Categorical columns frequently contain typographic variants of the same value
("healthy control", "Healthy Control", "HC", "hc") that will be treated as
different levels unless normalized.

```python
# Python — find near-duplicate categories with skrub's deduplication
from skrub import deduplicate          # clusters similar strings
import pandas as pd

# Show suspicious near-duplicates in a categorical column
col = "diagnosis"
cats = df[col].dropna().unique()
print(f"Unique values in '{col}': {sorted(cats)}")

# deduplicate suggests a canonical form for each cluster
deduped = deduplicate(df[col])        # returns Series with normalized values
changes = (df[col] != deduped).sum()
print(f"  {changes} values would be recoded by deduplication")
```

```r
# R — stringdist for pairwise similarity
library(stringdist)
cats <- unique(na.omit(df$diagnosis))
dist_matrix <- stringdistmatrix(cats, cats, method = "jw")  # Jaro-Winkler
rownames(dist_matrix) <- colnames(dist_matrix) <- cats

# Flag pairs that are close but not identical
close_pairs <- which(dist_matrix > 0 & dist_matrix < 0.15, arr.ind = TRUE)
if (nrow(close_pairs) > 0) {
  cat("Near-duplicate category pairs:\n")
  print(data.frame(a = cats[close_pairs[, 1]], b = cats[close_pairs[, 2]]))
}
```

---

## 5. Outlier detection

**For numeric columns, apply before analysis — not just for visualization.**
Outliers in a key column (e.g., a subject ID stored as an integer with one value
of 99999) will silently fail a join.

```python
# Python — IQR and z-score, language-agnostic logic
import pandas as pd, numpy as np
from scipy import stats

def flag_outliers(df: pd.DataFrame, z_thresh=3.5, iqr_mult=3.0) -> pd.DataFrame:
    """Return a summary of outlier counts per numeric column."""
    rows = []
    for col in df.select_dtypes("number").columns:
        s = df[col].dropna()
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        z = np.abs(stats.zscore(s))
        n_iqr = ((s < q1 - iqr_mult * iqr) | (s > q3 + iqr_mult * iqr)).sum()
        n_z   = (z > z_thresh).sum()
        rows.append({"column": col, "n_iqr_outliers": n_iqr, "n_zscore_outliers": n_z,
                     "min": s.min(), "median": s.median(), "max": s.max()})
    return pd.DataFrame(rows).query("n_iqr_outliers > 0 or n_zscore_outliers > 0")

print(flag_outliers(df))
```

```r
# R — IQR-based outlier flagging
flag_outliers_r <- function(df, iqr_mult = 3.0) {
  library(dplyr)
  df |>
    select(where(is.numeric)) |>
    summarise(across(everything(), list(
      n_outliers = ~{
        q <- quantile(., c(0.25, 0.75), na.rm = TRUE)
        iqr <- q[2] - q[1]
        sum(. < q[1] - iqr_mult * iqr | . > q[2] + iqr_mult * iqr, na.rm = TRUE)
      },
      min   = ~min(., na.rm = TRUE),
      max   = ~max(., na.rm = TRUE)
    )))
}
flag_outliers_r(df)
```

```julia
# Julia — IQR outlier count per numeric column
using Statistics, DataFrames

function flag_outliers(df::DataFrame; iqr_mult=3.0)
    results = []
    for col in names(df)
        s = skipmissing(df[!, col])
        eltype(collect(s)) <: Number || continue
        vals = collect(s)
        q1, q3 = quantile(vals, 0.25), quantile(vals, 0.75)
        iqr = q3 - q1
        n_out = count(v -> v < q1 - iqr_mult*iqr || v > q3 + iqr_mult*iqr, vals)
        n_out > 0 && push!(results, (col=col, n_outliers=n_out,
                                     min=minimum(vals), max=maximum(vals)))
    end
    results
end
flag_outliers(df)
```

---

## 6. Cross-field consistency

**Why it matters:** A birthdate after a scan date, a negative age, a subject coded
as "healthy control" with a non-zero symptom score — these are data errors that a
merge will propagate silently into analysis.

Define rules as assertions. Run them after every merge.

```python
# Python — assertion-based cross-field checks
import pandas as pd

def run_consistency_checks(df: pd.DataFrame) -> None:
    errors = []

    # Temporal: acquisition must be after birth (if both present)
    if {"birth_date", "scan_date"} <= set(df.columns):
        bad = (pd.to_datetime(df["scan_date"]) < pd.to_datetime(df["birth_date"])).sum()
        if bad: errors.append(f"  {bad} rows: scan_date before birth_date")

    # Logical: age must be positive
    if "age" in df.columns:
        bad = (df["age"] < 0).sum()
        if bad: errors.append(f"  {bad} rows: negative age")

    # Referential: all values in a coded column must be in the expected set
    if "diagnosis" in df.columns:
        valid_dx = {"HC", "SZ", "BD", "MDD"}
        bad_vals = set(df["diagnosis"].dropna().unique()) - valid_dx
        if bad_vals: errors.append(f"  Unknown diagnosis codes: {bad_vals}")

    if errors:
        print("CONSISTENCY FAILURES:")
        for e in errors: print(e)
    else:
        print("All consistency checks passed.")

run_consistency_checks(df)
```

```r
# R — dplyr filter-based consistency checks
library(dplyr)

check_consistency <- function(df) {
  issues <- list()

  # Temporal
  if (all(c("birth_date", "scan_date") %in% names(df))) {
    bad <- df |> filter(as.Date(scan_date) < as.Date(birth_date)) |> nrow()
    if (bad > 0) issues <- c(issues, sprintf("%d rows: scan_date before birth_date", bad))
  }

  # Logical
  if ("age" %in% names(df)) {
    bad <- df |> filter(age < 0) |> nrow()
    if (bad > 0) issues <- c(issues, sprintf("%d rows: negative age", bad))
  }

  # Referential
  if ("diagnosis" %in% names(df)) {
    valid_dx <- c("HC", "SZ", "BD", "MDD")
    bad_vals <- setdiff(na.omit(unique(df$diagnosis)), valid_dx)
    if (length(bad_vals) > 0)
      issues <- c(issues, paste("Unknown diagnosis codes:", paste(bad_vals, collapse=", ")))
  }

  if (length(issues) == 0) cat("All consistency checks passed.\n")
  else { cat("CONSISTENCY FAILURES:\n"); cat(paste0("  ", issues, "\n")) }
}
check_consistency(df)
```

---

## 7. Fuzzy key matching

Use when merge keys are structurally correct but contain typographic variants,
whitespace differences, or case inconsistencies that prevent an exact join.

**Diagnose first:** if key coverage is < 100% after an exact join, check whether
the unmatched keys are near-matches before concluding the files are unrelated.

### Python — skrub fuzzy_join

```python
from skrub import fuzzy_join
import pandas as pd

# Basic fuzzy join on a single key column
merged = fuzzy_join(
    left,  right,
    on="subject_id",          # or left_on=..., right_on=... for different names
    max_dist=0.3,             # reject matches beyond this distance (0=exact, 1=anything)
    add_match_info=True,      # adds skrub_left_key, skrub_right_key, skrub_distance columns
    suffix="_right",
)

# Inspect match quality before accepting results
print(merged[["skrub_left_key", "skrub_right_key", "skrub_distance"]].head(20))

# Drop rows where no close match was found
merged = fuzzy_join(left, right, on="subject_id", max_dist=0.3, drop_unmatched=True)
```

Key parameters:
- `max_dist`: distance threshold (after rescaling); start at 0.3 and tighten
- `add_match_info=True`: always use this first to audit what got matched to what
- `ref_dist`: controls how distance is rescaled; `"second_neighbor"` is robust for
  datasets where most strings are similar length

### R — fuzzyjoin

```r
library(fuzzyjoin)
library(stringr)

# Jaro-Winkler distance join (good for short identifiers)
merged <- stringdist_join(
  left, right,
  by = "subject_id",
  method = "jw",          # Jaro-Winkler; alternatives: lv (Levenshtein), osa, cosine
  max_dist = 0.1,         # fraction, not absolute count
  mode = "left",
  distance_col = "match_dist"
)

# Audit: show unmatched rows
unmatched <- merged |> filter(is.na(match_dist) | match_dist > 0.05)
print(unmatched)
```

### Julia — StringDistances.jl

```julia
using StringDistances, DataFrames

function fuzzy_join_jl(left::DataFrame, right::DataFrame,
                       left_col::String, right_col::String;
                       max_dist::Float64=0.2)
    lkeys = left[:, left_col]
    rkeys = right[:, right_col]
    matches = Vector{Union{Int, Missing}}(missing, nrow(left))
    dists   = Vector{Float64}(undef, nrow(left))
    for (i, lk) in enumerate(lkeys)
        best_j, best_d = 0, Inf
        for (j, rk) in enumerate(rkeys)
            d = StringDistances.evaluate(JaroWinkler(), string(lk), string(rk))
            if d < best_d; best_j, best_d = j, d; end
        end
        if best_d <= max_dist
            matches[i] = best_j
            dists[i]   = best_d
        end
    end
    hcat(left, DataFrame(right_match_idx=matches, match_dist=dists))
end
```

**When to use fuzzy matching vs. normalization:**
- Prefer explicit normalization (strip prefixes, lowercase, zero-pad) for
  structured identifiers like BIDS IDs — it produces a deterministic, auditable
  transform.
- Use fuzzy matching for free-text fields (site names, institution names, diagnoses
  entered as free text) where normalization rules are hard to enumerate.
- Always verify fuzzy matches manually with `add_match_info=True` (Python) or
  `distance_col=` (R) before accepting them. A fuzzy join is a hypothesis, not a fact.
