# Report Sections

Standard section order and cell templates for a statistical analysis report.
The goal is a notebook that reads like a methods + results section: reproducible,
self-contained, and structured so another analyst can follow the logic.

---

## Section order

```
0. Setup          — imports, constants, load data + dictionary
1. Data summary   — shape, dtype audit, missingness, distributions
2. QC             — method-specific diagnostic plots
3. Models         — hierarchical model sequence + comparison table
4. Results        — coefficient table, effect sizes, post-hoc contrasts
5. Figures        — main visualisation(s)
6. Conclusions    — plain-language summary, limitations, next steps
```

---

## Section 0: Setup

Purpose: reproducible environment declaration. Every path and dependency lives here
so someone cloning the repo can run the notebook without hunting for hardcoded paths.

```python
# %% [markdown]
# # Analysis Report: [Title]
#
# **Date:** YYYY-MM-DD  **Author:** [name]
#
# Brief one-paragraph description of the analysis goal.

# %% Setup
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import statsmodels.api as sm

# Paths — edit these to match your file locations
DATA_DIR   = Path("path/to/data")
INPUT_TSV  = DATA_DIR / "merged.tsv"
DICT_JSON  = DATA_DIR / "merged_data_dictionary.json"
OUTPUT_DIR = DATA_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

# Load data
df = pd.read_csv(INPUT_TSV, sep="\t")
print(f"Loaded: {df.shape[0]} rows x {df.shape[1]} columns")

# Load data dictionary (optional but useful for labelling)
import json
with open(DICT_JSON) as f:
    data_dict = json.load(f)
```

---

## Section 1: Data Summary

Purpose: confirm the data loaded correctly and document any pre-analysis decisions
(outlier exclusions, imputation choices). This section replaces prose descriptions
of the dataset in the methods section.

```python
# %% [markdown]
# ## 1. Data Summary

# %% 1a — Shape and dtypes
print(df.dtypes)
df.describe(include="all").T

# %% 1b — Missingness
missing = df.isnull().mean().sort_values(ascending=False)
missing = missing[missing > 0]
if missing.empty:
    print("No missing values.")
else:
    print(missing.to_string())
    # Visual missingness heatmap (requires missingno: pip install missingno)
    # import missingno as msno
    # msno.heatmap(df)

# %% 1c — Distribution of outcome variable(s)
# Replace 'outcome' with your actual outcome column name
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
df["outcome"].hist(ax=axes[0], bins=30, edgecolor="white")
axes[0].set_title("Outcome distribution"); axes[0].set_xlabel("outcome")

import scipy.stats as stats
stats.probplot(df["outcome"].dropna(), plot=axes[1])
axes[1].set_title("Q-Q plot of outcome")
plt.tight_layout(); plt.show()

# %% 1d — Key predictor distributions
# df[["group", "age", "score"]].describe()
# pd.crosstab(df["group"], df["site"]) if categorical predictors
```

---

## Section 2: QC

Purpose: verify model assumptions *before* fitting the final model. Document any
violations and the decision made in response (transformation, robust estimator, etc.).

The specific plots depend on the statistical method. See `qc-metrics.md` for the
must-run plots per method family. Below is a placeholder template:

```python
# %% [markdown]
# ## 2. Quality Control
#
# List the assumption checks relevant to [method] and what each showed.

# %% 2a — Pre-modelling: VIF / collinearity
# from statsmodels.stats.outliers_influence import variance_inflation_factor
# vif_data = pd.DataFrame()
# vif_data["feature"] = X.columns
# vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(len(X.columns))]
# print(vif_data)

# %% 2b — Post-fitting diagnostics (fill in after fitting models in Section 3)
# For OLS / ANOVA / LME:
#   from plugins.stat_analysis references.python_patterns import plot_residuals
#   plot_residuals(model_final)
#
# For logistic:
#   [ROC curve, calibration plot — see qc-metrics.md]
#
# For LME:
#   [Caterpillar plot of random intercepts — see qc-metrics.md]
```

---

## Section 3: Models

Purpose: the hierarchical model sequence from `plan-analysis`. Each level is fitted
and compared to the previous one so that the contribution of each term is isolated.

```python
# %% [markdown]
# ## 3. Models
#
# Hierarchical sequence: null → covariates → main effects → interaction.
# Comparison test: [F-test / LRT — specify which and why].

# %% 3a — Null model
m0 = smf.ols("outcome ~ 1", data=df).fit()

# %% 3b — Covariates
m1 = smf.ols("outcome ~ age + C(site)", data=df).fit()

# %% 3c — Main effects
m2 = smf.ols("outcome ~ age + C(site) + C(group) + score", data=df).fit()

# %% 3d — Interaction
m3 = smf.ols("outcome ~ age + C(site) + C(group) * score", data=df).fit()

# %% 3e — Model comparison table
sm.stats.anova_lm(m0, m1, m2, m3)
# Or use format_model_table() from python-patterns.md
```

---

## Section 4: Results

Purpose: report the final model's parameter estimates with confidence intervals,
effect sizes, and post-hoc contrasts. This section maps to the Results section of
a paper.

```python
# %% [markdown]
# ## 4. Results
#
# Report coefficients, CIs, and effect sizes for the final model.

# %% 4a — Final model summary
print(m3.summary())

# %% 4b — Coefficient table with 95% CIs
coef_table = pd.DataFrame({
    "Coefficient": m3.params,
    "CI_lower":    m3.conf_int()[0],
    "CI_upper":    m3.conf_int()[1],
    "p_value":     m3.pvalues,
})
print(coef_table.round(3))

# %% 4c — Effect sizes
# For ANOVA-style tests: compute eta-squared or omega-squared
# For regression: report standardised betas (fit model on z-scored predictors)
# For logistic: report odds ratios — np.exp(coef_table["Coefficient"])

# %% 4d — Post-hoc contrasts (if categorical predictors)
# Use emmeans in R, or statsmodels contrast for Python:
# from statsmodels.stats.multicomp import pairwise_tukeyhsd
# tukey = pairwise_tukeyhsd(df["outcome"], df["group"])
# print(tukey.summary())
```

---

## Section 5: Figures

Purpose: one or two main visualisations that communicate the key finding. Choose
based on the analysis type:

| Analysis | Recommended figure |
|---|---|
| ANOVA / factorial | Estimated marginal means with CIs; interaction plot |
| Regression | Partial regression plot; effect plot for the key predictor |
| Logistic | ROC curve; predicted probability by group |
| LME / RM | Spaghetti plot (individual trajectories) + group mean ± SE |
| MANOVA / CCA | Ordination biplot (first two canonical axes) |
| EFA | Factor loading heatmap; scree plot |

```python
# %% [markdown]
# ## 5. Main Figure

# %% 5a — [Describe figure here]
fig, ax = plt.subplots(figsize=(7, 5))
# ... plotting code ...
ax.set_title("[Figure title]")
ax.set_xlabel("[x label]"); ax.set_ylabel("[y label]")
plt.tight_layout()
fig.savefig(OUTPUT_DIR / "figure_main.png", dpi=150, bbox_inches="tight")
plt.show()
```

---

## Section 6: Conclusions

Purpose: plain-language summary for collaborators, plus explicit statement of
limitations and next steps.

```python
# %% [markdown]
# ## 6. Conclusions
#
# ### Main findings
# - [Finding 1 in plain language, with effect size and significance]
# - [Finding 2 ...]
#
# ### Limitations
# - [Sample size / power considerations]
# - [Assumption violations and how they were addressed]
# - [Generalisability concerns]
#
# ### Next steps
# - [Model extension or sensitivity analysis]
# - [Replication in independent dataset]
# - [Formal SEM / mediation analysis if suggested by plan-analysis]
```
