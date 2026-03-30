# Factor Analysis and Latent Variable Methods

Covers: exploratory factor analysis (EFA), confirmatory factor analysis (CFA),
principal component analysis (PCA as a data reduction tool), and the boundary of
structural equation modelling (SEM). These methods apply when you suspect that
observed variables are indicators of underlying latent constructs.

---

## When to use which method

| Method | Use when | Key distinction |
|---|---|---|
| PCA | You want to reduce many correlated variables to a smaller set of orthogonal composites. No theory about latent variables. | Components are mathematical summaries, not latent causes. |
| EFA | You believe latent factors exist and drive observed correlations, but you don't know the factor structure. Theory is being formed. | Factors are latent constructs; factor loadings are regressions. |
| CFA | You have a prior hypothesis about which variables load on which factors (from theory, prior EFA, or literature). | Hypothesis-testing mode; model fit is formally evaluated. |
| SEM | You have a CFA structure AND hypothesise directional paths between latent variables (mediation, moderation). | Combines measurement model (CFA) + structural model (regression). |

**The typical progression:**
1. No prior structure → EFA to discover the factor structure
2. EFA result → CFA in a new sample to confirm
3. CFA confirmed → SEM to model relationships between latent variables

Do not use CFA to "confirm" factors discovered in the same dataset used for EFA.
If you have only one dataset, split it: EFA on half, CFA on the other half.

---

## PCA

### When to use
- Dimensionality reduction before a regression or classification
- Creating composite scores when the latent variable model assumption is
  unnecessary or untestable
- Visualising high-dimensional data in 2D / 3D

### Key decisions
1. Covariance vs correlation matrix? → Always use correlation (standardise first)
   unless variables are on the same scale.
2. How many components to retain? → Scree plot elbow + Kaiser criterion (eigenvalue > 1)
   as a starting point; parallel analysis is more rigorous.

```r
pca <- prcomp(df[, vars], scale. = TRUE)
summary(pca)          # proportion of variance per component
screeplot(pca, type = "lines")
biplot(pca)           # variable loadings + subject scores

# Retain k components
scores <- pca$x[, 1:k]   # use as new predictors
```

```python
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

X = StandardScaler().fit_transform(df[vars])
pca = PCA()
pca.fit(X)

# Scree plot
plt.plot(np.cumsum(pca.explained_variance_ratio_))
plt.xlabel("Components"); plt.ylabel("Cumulative variance")
plt.show()

k = 3   # chosen number
scores = PCA(n_components=k).fit_transform(X)
```

---

## Exploratory Factor Analysis (EFA)

### Key decisions
1. **Extraction method:** Maximum likelihood (ML) — preferred because it enables
   formal fit tests. Principal axis factoring (PAF) if data are non-normal.
2. **Rotation:**
   - Oblique (promax, oblimin) when factors are expected to correlate — usually
     the right default for psychological/neuroimaging constructs.
   - Orthogonal (varimax) only when factors are genuinely uncorrelated.
3. **Number of factors:** Parallel analysis (most defensible) + scree plot + theoretical
   interpretability. Retain factors with eigenvalue > 1 only as a rough guide.
4. **Minimum loading threshold:** |loading| ≥ 0.30 to be interpreted (some fields use 0.40).
5. **Sample size requirement:** ≥ 5–10 observations per variable; N > 200 is preferable.

### Model hierarchy for EFA

```
Step 0: Assess factorability — KMO (> 0.6) and Bartlett's test of sphericity
Step 1: Parallel analysis to estimate number of factors
Step 2: Fit 1-factor model; examine residuals and fit indices
Step 3: Fit k-factor model (k from parallel analysis)
Step 4: Fit k+1 model to check if additional factor improves fit
Step 5: Examine loadings, cross-loadings, and communalities; name factors
```

```r
library(psych)
library(GPArotation)   # required for oblique rotation

# Step 0: Factorability
KMO(df[, vars])              # Kaiser-Meyer-Olkin ≥ 0.6
cortest.bartlett(df[, vars]) # Bartlett's test of sphericity

# Step 1: Parallel analysis
fa.parallel(df[, vars], fm = "ml", fa = "fa")

# Step 2-4: Fit models
fa_1 <- fa(df[, vars], nfactors = 1, fm = "ml", rotate = "oblimin")
fa_k <- fa(df[, vars], nfactors = k, fm = "ml", rotate = "oblimin")
fa_k1 <- fa(df[, vars], nfactors = k+1, fm = "ml", rotate = "oblimin")

# Compare fit
fa_k$RMSEA          # < 0.05 good, < 0.08 acceptable
fa_k$TLI            # > 0.95 good
fa_k$BIC            # lower is better
fa.diagram(fa_k)    # visual of factor loadings

# Loadings table (show only |loading| ≥ 0.30)
print(fa_k$loadings, cutoff = 0.30)
```

```python
from factor_analyzer import FactorAnalyzer, calculate_kmo, calculate_bartlett_sphericity

# Factorability
kmo_all, kmo_model = calculate_kmo(df[vars])
chi_sq, p_val = calculate_bartlett_sphericity(df[vars])
print(f"KMO: {kmo_model:.3f}")

# EFA
fa = FactorAnalyzer(n_factors=k, method="ml", rotation="oblimin")
fa.fit(df[vars])

# Factor loadings
import pandas as pd
loadings = pd.DataFrame(fa.loadings_, index=vars, columns=[f"F{i+1}" for i in range(k)])
print(loadings[loadings.abs() >= 0.30])

# Eigenvalues (for scree)
ev, v = fa.get_eigenvalues()
```

---

## Confirmatory Factor Analysis (CFA)

### Key decisions
1. **Model specification** — which observed variables load on which factors, and
   which cross-loadings (if any) are allowed.
2. **Identification** — each factor needs ≥ 3 indicators; fix factor variance to 1
   or fix one loading to 1 for scale identification.
3. **Estimator** — ML (normal data), WLSMV (ordinal indicators), MLR (non-normal
   continuous, robust SEs).
4. **Model fit criteria** — CFI/TLI > 0.95, RMSEA < 0.06, SRMR < 0.08 for good fit.

### Model hierarchy for CFA

```
Level 0: Null model (no factors; used for CFI calculation only)
Level 1: Hypothesised factor structure
Level 2: Modified model (based on modification indices, if needed)
```

```r
library(lavaan)

# Define the measurement model
model <- "
  Factor1 =~ item1 + item2 + item3
  Factor2 =~ item4 + item5 + item6
"

fit <- cfa(model, data = df, estimator = "ML")
summary(fit, fit.measures = TRUE, standardized = TRUE)

# Fit indices
fitMeasures(fit, c("cfi", "tli", "rmsea", "srmr", "aic", "bic"))

# Modification indices (use cautiously; only modify with theory)
modificationIndices(fit, sort = TRUE, maximum.number = 10)

# Standardised loadings
standardizedSolution(fit)[standardizedSolution(fit)$op == "=~", ]
```

```python
from semopy import Model    # pip install semopy

model_spec = """
Factor1 =~ item1 + item2 + item3
Factor2 =~ item4 + item5 + item6
"""
model = Model(model_spec)
res = model.fit(df[items])
print(model.inspect(std_est=True))   # standardised loadings
```

---

## Fit indices quick reference

| Index | Threshold for acceptable fit | Notes |
|---|---|---|
| CFI | ≥ 0.95 | 0 = null model, 1 = perfect fit |
| TLI (NNFI) | ≥ 0.95 | Penalises for model complexity |
| RMSEA | ≤ 0.06 (≤ 0.08 acceptable) | Confidence interval should include values ≤ 0.05 |
| SRMR | ≤ 0.08 | Standardised mean squared residual |
| AIC / BIC | Lower is better | For model comparison, not absolute fit |

Poor fit → inspect residual correlation matrix and modification indices.
Do not add modifications without theoretical justification.

---

## SEM skeleton (when to escalate)

SEM extends CFA by adding directional (regression) paths between latent variables.
Use SEM when:
- You have confirmed factor structures for both predictor and outcome constructs
- You hypothesise a mediation path through a latent mediator
- You want to test indirect effects (bootstrapped CIs)

This skill generates the CFA measurement model and flags the need for a full SEM
workflow. It does not specify path models — that requires detailed theory and is
best handled as a dedicated analysis session.

```r
# SEM skeleton (lavaan) — fill in paths from theory
sem_model <- "
  # Measurement model (from confirmed CFA)
  LatentA =~ item1 + item2 + item3
  LatentB =~ item4 + item5 + item6

  # Structural model (paths between latents)
  LatentB ~ LatentA         # A predicts B
  outcome ~ LatentB + age   # B predicts outcome, controlling for age
"
sem_fit <- sem(sem_model, data = df, estimator = "ML")
summary(sem_fit, fit.measures = TRUE, standardized = TRUE)
```

---

## Assumption checks

| Method | Assumption | Check |
|---|---|---|
| PCA / EFA / CFA | No severe multivariate outliers | Mahalanobis distance |
| EFA / CFA | Sufficient sample size | N ≥ 5–10 per variable; N > 200 overall |
| EFA | Adequate variable intercorrelations | KMO ≥ 0.6; Bartlett significant |
| CFA | Multivariate normality (for ML estimator) | Mardia's test; if violated → use MLR or WLSMV |
| CFA | Local independence | Residual correlations should be small (< 0.10) |

---

## When to escalate

- Ordinal indicators (Likert) → use WLSMV estimator in lavaan: `estimator = "WLSMV"`
- Non-normal continuous indicators → use MLR: `estimator = "MLR"`
- Longitudinal factor structure → growth curve model (out of scope)
- Complex mediation with latent variables → full SEM session (out of scope)
- Latent class analysis (categorical latent variable) → out of scope; name it
