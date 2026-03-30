# Jupytext Configuration

Jupytext lets you maintain notebooks as plain text scripts (`.py`, `.R`, `.jl`)
that pair with `.ipynb` files. The text file is what you commit to git; the
notebook is generated on demand. This makes diffs readable and avoids large binary
blobs in version history.

---

## Choosing a format

| Format | Extension | Use when |
|---|---|---|
| Percent (`# %%`) | `.py` / `.R` / `.jl` | Default — clean, readable, works with most editors |
| Light script | `.py` | Minimal metadata; good for scripts that also run standalone |
| MyST Markdown | `.md` | When you want prose-heavy notebooks with embedded code |

**Recommend percent format** for analysis reports — it has clear cell delimiters,
supports cell metadata, and renders well in VS Code, JupyterLab, and Spyder.

---

## Required header (Python percent format)

Every `.py` report file must begin with this metadata block:

```python
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---
```

For R (`.R` percent format), replace the header with:

```r
# ---
# jupyter:
#   jupytext:
#     formats: ipynb,r:percent
#     text_representation:
#       extension: .R
#       format_name: percent
#   kernelspec:
#     display_name: R
#     language: R
#     name: ir
# ---
```

---

## Cell delimiters

```python
# %% [markdown]
# ## Section heading
# Prose text goes here.

# %%
# Code cell — just a comment + code block
import pandas as pd
df = pd.read_csv("merged.tsv", sep="\t")
df.head()
```

Use `# %% [markdown]` for text cells and `# %%` for code cells. Cell titles
(shown in the outline panel) go after the `%%`:

```python
# %% Load data
df = pd.read_csv("merged.tsv", sep="\t")
```

---

## Conversion commands

```bash
# Convert .py to .ipynb (generate notebook from script)
jupytext --to notebook report.py

# Sync .py and .ipynb (update whichever is newer)
jupytext --sync report.py

# Convert all .py files in a directory
jupytext --to notebook *.py

# Set up automatic pairing via jupytext.toml (place at repo root)
# [formats]
# notebook = "ipynb,py:percent"
```

---

## Editor setup

- **VS Code**: Install the "Jupytext" extension; `.py` percent files open as notebooks.
- **JupyterLab**: `pip install jupyterlab-jupytext` — adds a Jupytext panel.
- **Jupyter Notebook classic**: `pip install jupytext` is sufficient; use File → Jupytext.

---

## Git workflow

Commit only the `.py` file. Add `.ipynb` to `.gitignore` (or commit it for output
sharing, but never for diffs). Regenerate the notebook locally before running:

```bash
jupytext --to notebook report.py
jupyter nbconvert --to notebook --execute report.ipynb
```
