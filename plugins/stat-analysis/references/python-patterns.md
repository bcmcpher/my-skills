# Python Patterns

Shared utility code for Python-based statistical analysis workflows. Load this
file when you need import blocks, model comparison helpers, or diagnostic plot
functions. Avoids re-implementing these in every generated script.

---

## Standard imports

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import scipy.stats as stats
import statsmodels.formula.api as smf
import statsmodels.api as sm
import statsmodels.graphics.gofplots as gof
from pathlib import Path
```

---

## Model comparison helpers

### Likelihood ratio test (GLM, GLMM, mixed effects)

```python
def lrt(restricted, full):
    """Likelihood ratio test between two nested models.

    Parameters
    ----------
    restricted : fitted model (statsmodels) with fewer parameters
    full       : fitted model with more parameters

    Returns
    -------
    (chi2_stat, p_value, df_diff)
    """
    stat = 2 * (full.llf - restricted.llf)
    df   = int(round(full.df_model - restricted.df_model))
    p    = stats.chi2.sf(stat, df)
    print(f"LRT: χ²({df}) = {stat:.3f}, p = {p:.4f}")
    return stat, p, df
```

### Incremental F-test (OLS, ANOVA)

```python
def f_test(restricted, full):
    """Incremental F-test between two nested OLS models.

    Parameters
    ----------
    restricted : fitted OLS model with fewer parameters
    full       : fitted OLS model with more parameters

    Returns
    -------
    (F_stat, p_value)
    """
    rss_r = restricted.ssr;  df_r = restricted.df_resid
    rss_f = full.ssr;        df_f = full.df_resid
    F = ((rss_r - rss_f) / (df_r - df_f)) / (rss_f / df_f)
    p = stats.f.sf(F, df_r - df_f, df_f)
    print(f"F({int(df_r - df_f)}, {int(df_f)}) = {F:.3f}, p = {p:.4f}")
    return F, p
```

---

## Diagnostic plot helpers

### 4-panel residuals plot (OLS / ANOVA / LME fixed-effect residuals)

```python
def plot_residuals(result, title="Residual Diagnostics"):
    """Standard 4-panel diagnostic plot for a fitted statsmodels OLS/GLM result.

    Panels: residuals vs fitted, Q-Q, scale-location, residuals vs leverage.
    """
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle(title)

    fitted   = result.fittedvalues
    residuals = result.resid
    std_resid = residuals / residuals.std()
    influence = result.get_influence()

    # Residuals vs fitted
    axes[0, 0].scatter(fitted, residuals, alpha=0.4, s=15)
    axes[0, 0].axhline(0, color="red", linewidth=0.8)
    axes[0, 0].set_xlabel("Fitted values"); axes[0, 0].set_ylabel("Residuals")
    axes[0, 0].set_title("Residuals vs Fitted")

    # Q-Q plot
    gof.qqplot(residuals, line="s", ax=axes[0, 1])
    axes[0, 1].set_title("Normal Q-Q")

    # Scale-location
    axes[1, 0].scatter(fitted, np.sqrt(np.abs(std_resid)), alpha=0.4, s=15)
    axes[1, 0].set_xlabel("Fitted values"); axes[1, 0].set_ylabel("√|Std. residuals|")
    axes[1, 0].set_title("Scale-Location")

    # Residuals vs leverage
    leverage = influence.hat_matrix_diag
    axes[1, 1].scatter(leverage, std_resid, alpha=0.4, s=15)
    axes[1, 1].axhline(0, color="red", linewidth=0.8)
    axes[1, 1].set_xlabel("Leverage"); axes[1, 1].set_ylabel("Std. residuals")
    axes[1, 1].set_title("Residuals vs Leverage")

    plt.tight_layout()
    plt.show()
    return fig
```

---

## Model summary table helper

```python
def format_model_table(models, labels=None):
    """Print a comparison table for a sequence of nested models.

    Parameters
    ----------
    models : list of fitted statsmodels result objects
    labels : list of strings, e.g. ["Null", "Covariates", "Main effects"]
    """
    if labels is None:
        labels = [f"Model {i}" for i in range(len(models))]
    rows = []
    for label, m in zip(labels, models):
        rows.append({
            "Model":  label,
            "N params": int(m.df_model + 1),
            "Log-lik": f"{m.llf:.2f}",
            "AIC":     f"{m.aic:.2f}",
            "BIC":     f"{m.bic:.2f}",
        })
    print(pd.DataFrame(rows).to_string(index=False))
```
