# Input Data Formats

Reference for supported file formats, detection heuristics, and read commands
for Python, R, and Julia. Used by merge-data and merge-agent.

---

## Supported formats

| Extension(s) | Format | Detection method | Notes |
|---|---|---|---|
| `.csv` | Comma-separated values | Extension + sniff first line | May use other delimiters despite `.csv` name |
| `.tsv` | Tab-separated values | Extension | Rarely uses other delimiters |
| `.txt` | Generic text | Sniff delimiter | May be any delimiter; treat as CSV with sniffing |
| `.xlsx` | Excel (OpenXML) | Extension | Requires `openpyxl` in Python |
| `.xls` | Excel (legacy binary) | Extension | Requires `xlrd` ≤ 1.2 in Python; `readxl` in R |
| `.xlsm` | Excel with macros | Extension | Treat as `.xlsx`; macros are not executed |
| `.parquet` | Apache Parquet | Extension | Requires `pyarrow` or `fastparquet` |
| `.feather` | Feather / Arrow IPC | Extension | Requires `pyarrow` |
| `.h5`, `.hdf5` | HDF5 | Extension | Requires `tables` (PyTables); check key name |
| `.json` | JSON (records or columns) | Extension | Only if tabular structure; check orientation |
| `.jsonl`, `.ndjson` | Newline-delimited JSON | Extension | One JSON object per line |

Files with none of the above extensions should be skipped and reported to the user by name.

---

## Delimiter detection for text formats

Apply in order:

1. Check extension: `.tsv` → tab; `.csv` → comma (but verify with step 2).
2. Read the first 2000 bytes and apply `csv.Sniffer().sniff(sample)` in Python.
3. If sniffing fails or is ambiguous, count occurrences of `,`, `\t`, `;`, `|` in the
   first non-blank line; use whichever is most frequent.
4. If still ambiguous, default to comma and add a comment in the generated script
   noting the assumption.

---

## Encoding detection for text formats

1. Try UTF-8. If `UnicodeDecodeError` occurs, try `latin-1` (ISO-8859-1).
2. For robust detection, apply `chardet.detect(raw_bytes)` on the first 4096 bytes.
3. Always specify `encoding=` explicitly in the read call — never rely on the
   platform default.

Common encodings in practice:
- BIDS-compliant files: UTF-8 (required by spec)
- Files exported from Excel on Windows: often `cp1252` (Western European Windows)
- Files exported from macOS Numbers: sometimes `mac_roman`
- Legacy clinical/neuroimaging exports: often `latin-1`

---

## Python read commands

```python
import pandas as pd

# ── Text formats ────────────────────────────────────────────────────────────────
df = pd.read_csv("file.csv", sep=",", encoding="utf-8")
df = pd.read_csv("file.tsv", sep="\t", encoding="utf-8")
# Auto-detect delimiter (use engine="python" to enable sep=None)
df = pd.read_csv("file.txt", sep=None, engine="python", encoding="utf-8")

# ── Excel ───────────────────────────────────────────────────────────────────────
df = pd.read_excel("file.xlsx", sheet_name=0, engine="openpyxl")
df = pd.read_excel("file.xls",  sheet_name=0, engine="xlrd")
# List all sheet names before reading
sheet_names = pd.ExcelFile("file.xlsx").sheet_names

# ── Parquet ─────────────────────────────────────────────────────────────────────
df = pd.read_parquet("file.parquet")   # auto-selects pyarrow or fastparquet

# ── Feather ─────────────────────────────────────────────────────────────────────
df = pd.read_feather("file.feather")

# ── HDF5 — list keys first; default key is often "/data" or "/df" ───────────────
import tables  # noqa: F401  ensures PyTables backend is loaded
with pd.HDFStore("file.h5", "r") as store:
    keys = store.keys()   # e.g. ['/data', '/metadata']
df = pd.read_hdf("file.h5", key="/data")

# ── JSON ────────────────────────────────────────────────────────────────────────
df = pd.read_json("file.json",  orient="records")   # most common for tabular data
df = pd.read_json("file.json",  orient="columns")   # column-keyed dict of lists
df = pd.read_json("file.jsonl", lines=True)         # newline-delimited JSON
```

---

## R read commands

```r
library(readr)    # CSV/TSV/delimited
library(readxl)   # Excel
library(arrow)    # Parquet, Feather
library(jsonlite) # JSON
library(rhdf5)    # HDF5

# ── Text formats ────────────────────────────────────────────────────────────────
df <- read_csv("file.csv")                       # readr; auto-detects encoding
df <- read_tsv("file.tsv")
df <- read_delim("file.txt", delim = "\t")       # explicit delimiter

# ── Excel ───────────────────────────────────────────────────────────────────────
df <- read_excel("file.xlsx", sheet = 1)
df <- read_excel("file.xls",  sheet = 1)

# ── Parquet / Feather ───────────────────────────────────────────────────────────
df <- read_parquet("file.parquet")               # arrow
df <- read_feather("file.feather")               # arrow

# ── HDF5 ────────────────────────────────────────────────────────────────────────
h5ls("file.h5")                                  # list datasets
df <- as.data.frame(h5read("file.h5", "/data"))

# ── JSON ────────────────────────────────────────────────────────────────────────
df <- as.data.frame(fromJSON("file.json"))       # records array
```

---

## Julia read commands

```julia
using CSV, DataFrames, XLSX, Arrow, JSON3, HDF5

# ── Text formats ────────────────────────────────────────────────────────────────
df = CSV.read("file.csv", DataFrame)
df = CSV.read("file.tsv", DataFrame; delim='\t')
df = CSV.read("file.txt", DataFrame; delim='\t')     # specify if known

# ── Excel ───────────────────────────────────────────────────────────────────────
xf = XLSX.readxlsx("file.xlsx")
df = DataFrame(XLSX.eachtablerow(xf["Sheet1"]))

# ── Parquet — use Arrow.jl for Feather; native Parquet via Parquet2.jl ──────────
df = DataFrame(Arrow.Table("file.feather"))

# ── HDF5 ────────────────────────────────────────────────────────────────────────
fid = h5open("file.h5", "r")
data = read(fid, "data")
close(fid)
df = DataFrame(data)

# ── JSON (records array) ────────────────────────────────────────────────────────
records = JSON3.read(read("file.json", String))
df = DataFrame(records)
```

---

## Common gotchas

| Symptom | Likely cause | Fix |
|---|---|---|
| `UnicodeDecodeError` on read | Non-UTF-8 encoding | Try `encoding="latin-1"` or use `chardet` |
| Extra blank column at end | Trailing delimiter in every row | `pd.read_csv(..., index_col=False)` |
| All data lands in one column | Wrong delimiter | Sniff or specify `sep` explicitly |
| Numbers read as strings | Thousands-separator comma in numeric column | `pd.read_csv(..., thousands=",")` |
| Dates read as floats | Excel serial date format (days since 1899-12-30) | `pd.to_datetime(df["date"], unit="D", origin="1899-12-30")` |
| Mixed types / unexpected NaN | Blank cells mixed with values | `pd.read_csv(..., na_values=["", " ", "NA", "N/A", "nan", "."])` |
| Duplicate column names | Two columns share the same header | pandas auto-appends `.1`; log this as a warning and rename explicitly |
| Wrong Excel sheet read | Default `sheet_name=0` is not the data sheet | List `pd.ExcelFile(path).sheet_names` and select the correct one |
| HDF5 key not found | File written with a non-default key name | List keys with `pd.HDFStore(path).keys()` before reading |
| Parquet fails to load | Wrong engine installed | Try `pd.read_parquet(..., engine="pyarrow")` or `engine="fastparquet"` |
| CSV row counts differ by 1 | Header row miscounted | Verify `header=0` (default) or `header=None` if no header row |
