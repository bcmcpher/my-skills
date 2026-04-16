# Shared Diagnostics and Assumption Checks

Standard QC checks applicable across model families. Each method reference
(anova-family.md, regression-glm.md, etc.) lists which of these to apply and when.

---

## Pre-modelling checks (run before fitting any model)

### Missingness
- Compute missing fraction per variable.
- If > 5% missing on any predictor or outcome, discuss with user: listwise deletion
  (default), mean/mode imputation (quick but biases SEs), or multiple imputation (MI).
- Check whether missingness is random (MCAR) or systematic (MAR/MNAR) by correlating
  a missingness indicator with other variables.

### Outliers
- Univariate: z-score > ±3.5 or IQR-based (Tukey fences at 1.5× IQR).
- Multivariate: Mahalanobis distance with chi-squared critical value (df = p, α = 0.001).
- Flag but do not automatically remove — ask the user about each outlier's origin.

### Distribution shape of the outcome
- Histogram + Q-Q plot.
- Shapiro-Wilk (N < 5000) or Kolmogorov-Smirnov (N ≥ 5000).
- Skewness > |1| and kurtosis > |3| → consider log/sqrt transform or GLM family.

### Collinearity among predictors
- Variance inflation factor (VIF): VIF > 5 is a concern; VIF > 10 is severe.
- Condition number of the design matrix: > 30 suggests numerical instability.
- Correlation matrix among continuous predictors: |r| > 0.8 → flag to user.

---

## Post-fitting diagnostics (run after each model level)

### Residual plots (OLS, ANOVA, LME)

| Plot | What to look for |
|---|---|
| Residuals vs fitted | No systematic trend; should be flat and evenly scattered |
| Q-Q plot of residuals | Points follow the diagonal; heavy tails → non-normality |
| Scale-location (√\|residuals\| vs fitted) | Flat line → homoscedasticity; fan shape → heteroscedasticity |
| Residuals vs leverage (Cook's D) | No points with high leverage AND high residual |

```r
# R: base plot method
par(mfrow = c(2, 2))
plot(model)

# Or with ggplot
library(ggfortify)
autoplot(model)
```

```python
# Python: statsmodels
import statsmodels.graphics.gofplots as gof
sm.graphics.plot_regress_exog(result, "predictor")
gof.qqplot(result.resid, line="s")
```

### Homogeneity of variance (ANOVA family)
- Levene's test: `car::leveneTest()` in R; `scipy.stats.levene()` in Python.
- Significant result → consider Welch's ANOVA (`oneway.test(var.equal=FALSE)`) or
  a heteroscedasticity-robust estimator (`sandwich` package in R).

### Normality of residuals
- Shapiro-Wilk on model residuals (not on raw outcome).
- For N > 5000, normality tests are almost always significant due to power — rely
  on Q-Q plots and skewness/kurtosis instead.
- LME: check normality of both residuals and random effects (BLUPs).

### Random effects diagnostics (mixed effects models)
- QQ plot of random effects (BLUPs): `qqnorm(ranef(model)$subject[,1])`
- Caterpillar plot of random intercepts to check for outlier subjects/groups.
- Intraclass correlation coefficient (ICC): proportion of variance at group level.
  ICC < 0.05 suggests random effects may not be necessary.

```r
# R: caterpillar plot of BLUPs +/- 95% CI
library(lattice)
dotplot(ranef(model, condVar = TRUE),
        scales = list(x = list(relation = "free")))

# ICC
performance::icc(model)
# Marginal R² (fixed effects only) and conditional R² (fixed + random)
MuMIn::r.squaredGLMM(model)
```

```python
# Python (statsmodels MixedLM): extract random effects
re = result.random_effects           # dict: group → random intercept
re_vals = pd.Series({k: v[0] for k, v in re.items()}, name="BLUP")
re_vals_sorted = re_vals.sort_values()

import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(4, max(4, len(re_vals) * 0.25)))
ax.scatter(re_vals_sorted, range(len(re_vals_sorted)), s=20)
ax.axvline(0, color="red", linewidth=0.8)
ax.set_yticks(range(len(re_vals_sorted)))
ax.set_yticklabels(re_vals_sorted.index, fontsize=7)
ax.set_xlabel("Random intercept BLUP")
ax.set_title("Caterpillar plot")
plt.tight_layout(); plt.show()
```

### GLM-specific diagnostics

| Family | Key check | Red flag |
|---|---|---|
| Binomial (logistic) | Hosmer-Lemeshow goodness of fit | p < 0.05 |
| Poisson | Dispersion = residual deviance / df | > 1.5 → overdispersion |
| All GLMs | Deviance residuals Q-Q plot | Systematic departure from normal |
| All GLMs | Pearson residuals vs fitted | Fan shape → wrong family or link |

#### ROC curve (logistic / GLMM binary)

```r
library(pROC)
roc_obj <- pROC::roc(df$outcome, fitted(model))
plot(roc_obj, print.auc = TRUE, main = "ROC curve")
# AUC >= 0.7 acceptable; >= 0.8 good; >= 0.9 excellent
```

```python
from sklearn.metrics import RocCurveDisplay
RocCurveDisplay.from_predictions(df["outcome"], result.predict())
plt.title(f"ROC (AUC = {result.pseudo_rsquared():.3f})")
plt.show()

# Or with actual AUC via sklearn:
from sklearn.metrics import roc_auc_score
auc = roc_auc_score(df["outcome"], result.predict())
print(f"AUC-ROC: {auc:.3f}")
```

#### Calibration plot — Hosmer-Lemeshow (logistic)

```r
library(ResourceSelection)
hoslem.test(model$y, fitted(model), g = 10)
# p > 0.05 indicates adequate calibration (model predictions match observed rates)

# Visual calibration: predicted probability deciles vs observed rates
breaks <- quantile(fitted(model), probs = seq(0, 1, by = 0.1))
df$decile <- cut(fitted(model), breaks = breaks, include.lowest = TRUE)
cal <- aggregate(cbind(observed = model$y, predicted = fitted(model)),
                 by = list(decile = df$decile), FUN = mean)
plot(cal$predicted, cal$observed, xlim = 0:1, ylim = 0:1,
     xlab = "Mean predicted probability", ylab = "Observed event rate",
     main = "Calibration plot")
abline(0, 1, col = "red")
```

```python
from sklearn.calibration import calibration_curve
prob_true, prob_pred = calibration_curve(df["outcome"], result.predict(), n_bins=10)
plt.figure(figsize=(5, 5))
plt.plot(prob_pred, prob_true, "s-")
plt.plot([0, 1], [0, 1], "r--")
plt.xlabel("Mean predicted probability"); plt.ylabel("Observed event rate")
plt.title("Calibration plot"); plt.show()
```

#### Rootogram (Poisson / negative binomial count models)

```r
library(countreg)   # install.packages("countreg", repos="http://R-Forge.R-project.org")
rootogram(model)
# Hanging bars below zero indicate over-prediction; above zero = under-prediction.
# If package unavailable, inspect observed vs fitted count frequencies manually:
obs_counts <- table(model$y)
pred_mean  <- mean(fitted(model))
# Compare empirical frequency table to Poisson(pred_mean) PMF
```

```python
import numpy as np
obs   = df["count"].value_counts().sort_index()
pred_mean = result.predict().mean()
k_range   = np.arange(obs.index.min(), obs.index.max() + 1)
from scipy.stats import poisson
expected  = poisson.pmf(k_range, pred_mean) * len(df)

fig, ax = plt.subplots()
ax.bar(k_range, np.sqrt(expected), label="Expected", alpha=0.6)
ax.bar(k_range, np.sqrt(obs.reindex(k_range, fill_value=0)),
       bottom=np.sqrt(expected) - np.sqrt(obs.reindex(k_range, fill_value=0)),
       label="Observed - Expected", alpha=0.6, color="orange")
ax.axhline(0, color="black", linewidth=0.8)
ax.set_xlabel("Count"); ax.set_ylabel("sqrt(frequency)")
ax.set_title("Rootogram"); ax.legend(); plt.show()
```

---

## EFA / PCA diagnostics

### Scree plot and parallel analysis

```r
library(psych)
# Combined scree + parallel analysis (psych package)
fa.parallel(df[, vars], fm = "ml", fa = "fa",
            main = "Parallel Analysis Scree Plot")
# The dashed line shows eigenvalues from random data; retain factors above it.
```

```python
from factor_analyzer import FactorAnalyzer
import matplotlib.pyplot as plt
import numpy as np

fa = FactorAnalyzer(n_factors=len(vars), rotation=None)
fa.fit(df[vars])
ev, _ = fa.get_eigenvalues()

# Scree plot with Kaiser criterion line
plt.figure(figsize=(8, 4))
plt.plot(range(1, len(ev) + 1), ev, "o-")
plt.axhline(1, color="red", linestyle="--", label="Kaiser criterion (eigenvalue = 1)")
plt.xlabel("Factor number"); plt.ylabel("Eigenvalue")
plt.title("Scree plot"); plt.legend(); plt.show()

# Parallel analysis approximation (random data permutation)
n_iter = 100
rand_ev = np.array([
    np.linalg.eigvalsh(np.corrcoef(np.random.randn(df.shape[0], len(vars)).T))[::-1]
    for _ in range(n_iter)
])
plt.figure(figsize=(8, 4))
plt.plot(range(1, len(ev) + 1), ev, "o-", label="Actual eigenvalues")
plt.plot(range(1, rand_ev.shape[1] + 1), rand_ev.mean(axis=0), "s--",
         label="Random data mean eigenvalue")
plt.axhline(1, color="grey", linestyle=":", linewidth=0.8)
plt.xlabel("Factor"); plt.ylabel("Eigenvalue")
plt.title("Parallel analysis"); plt.legend(); plt.show()
```

### Factor loading heatmap (EFA / CFA)

```r
library(ggplot2)
library(reshape2)

# Extract loadings matrix from a psych::fa object
loadings_mat <- as.data.frame(unclass(fa_k$loadings))
loadings_mat$variable <- rownames(loadings_mat)
loadings_long <- reshape2::melt(loadings_mat, id.vars = "variable",
                                variable.name = "factor", value.name = "loading")
# Suppress near-zero loadings visually
loadings_long$loading_show <- ifelse(abs(loadings_long$loading) >= 0.30,
                                     loadings_long$loading, NA)

ggplot(loadings_long, aes(x = factor, y = variable, fill = loading_show)) +
  geom_tile(color = "white") +
  geom_text(aes(label = round(loading_show, 2)), na.rm = TRUE, size = 3) +
  scale_fill_gradient2(low = "blue", mid = "white", high = "red",
                       midpoint = 0, limits = c(-1, 1), name = "Loading",
                       na.value = "grey90") +
  labs(title = "Factor loading heatmap (|loading| >= 0.30 shown)",
       x = NULL, y = NULL) +
  theme_minimal()
```

```python
import seaborn as sns
import pandas as pd

loadings = pd.DataFrame(
    fa.loadings_,
    index=vars,
    columns=[f"F{i+1}" for i in range(fa.n_factors)]
)
# Mask near-zero loadings
mask = loadings.abs() < 0.30

plt.figure(figsize=(max(4, fa.n_factors * 1.2), max(5, len(vars) * 0.4)))
sns.heatmap(loadings, mask=mask, annot=True, fmt=".2f",
            center=0, cmap="RdBu_r", vmin=-1, vmax=1,
            linewidths=0.4, cbar_kws={"label": "Loading"})
plt.title("Factor loading heatmap (|loading| >= 0.30 shown)")
plt.tight_layout(); plt.show()
```

---

## MANOVA diagnostics

### Multivariate normality (Henze-Zirkler test)

```r
library(MVN)    # install.packages("MVN")
mvn_result <- MVN::mvn(df[, dvs], mvnTest = "hz")
print(mvn_result$multivariateNormality)
# p > 0.05: fail to reject multivariate normality
# If violated: use Pillai's trace (most robust test statistic) rather than Wilks' lambda

# Visual: chi-squared Q-Q plot for Mahalanobis distances
MVN::mvn(df[, dvs], mvnTest = "hz", multivariatePlot = "qq")
```

```python
from scipy.spatial.distance import mahalanobis
import numpy as np

Y = df[dvs].values
cov = np.cov(Y.T)
cov_inv = np.linalg.pinv(cov)
mean = Y.mean(axis=0)
d2 = np.array([mahalanobis(row, mean, cov_inv)**2 for row in Y])

# Chi-squared Q-Q for Mahalanobis distances
from scipy.stats import chi2
theoretical = chi2.ppf(np.linspace(0.01, 0.99, len(d2)), df=Y.shape[1])
plt.figure(figsize=(5, 5))
plt.scatter(np.sort(theoretical), np.sort(d2), s=15, alpha=0.6)
plt.plot([0, theoretical.max()], [0, theoretical.max()], "r--")
plt.xlabel(f"Theoretical chi-squared ({Y.shape[1]} df)")
plt.ylabel("Mahalanobis distance squared")
plt.title("Multivariate normality Q-Q")
plt.show()
```

---

## Effect size and practical significance

Always report alongside p-values:

| Test | Effect size | Interpretation benchmarks |
|---|---|---|
| t-test / contrast | Cohen's d | 0.2 small, 0.5 medium, 0.8 large |
| ANOVA | η² or ω² | 0.01 small, 0.06 medium, 0.14 large |
| Regression | R², ΔR² per predictor | Depends heavily on field |
| Logistic | Odds ratio, AUC-ROC | OR > 2 or < 0.5 often meaningful |
| Mixed effects | Conditional R² (fixed + random) | `MuMIn::r.squaredGLMM()` in R |

---

## Multiple comparison correction

Applies whenever testing more than one hypothesis in the same analysis:

| Situation | Method |
|---|---|
| Few pre-specified contrasts | Bonferroni (conservative but simple) |
| Many comparisons, control FWER | Holm-Bonferroni (uniformly more powerful than Bonferroni) |
| Exploratory, control FDR | Benjamini-Hochberg (FDR ≤ 0.05) |
| Post-hoc contrasts after ANOVA | Tukey HSD (balanced); Games-Howell (unequal variances) |
| Planned orthogonal contrasts | No correction needed if pre-registered |

```r
# R: post-hoc with emmeans
library(emmeans)
emm <- emmeans(model, ~ group)
pairs(emm, adjust = "tukey")

# FDR on a vector of p-values
p.adjust(p_vector, method = "BH")
```

---

## Diagnostic plots quick-reference by method

| Method | Must-run plots |
|---|---|
| OLS / ANOVA | Residuals vs fitted, Q-Q, scale-location, Cook's D |
| LME | Residuals vs fitted, Q-Q of residuals, Q-Q of BLUPs, caterpillar |
| Logistic | ROC curve, calibration (Hosmer-Lemeshow), residuals vs fitted |
| Poisson | Residuals vs fitted, dispersion check, rootogram |
| MANOVA | Multivariate Q-Q (Henze-Zirkler test), Box's M for homogeneity of covariance |
| CCA | Triplot (sites, species, env), permutation distribution |
| EFA | Scree plot, parallel analysis, factor loading heatmap, communalities |
