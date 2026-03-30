# Multivariate Methods

Covers: canonical correlation analysis (CCA), redundancy analysis (RDA),
distance-based multivariate tests (PERMANOVA), and multivariate multiple
regression. These methods apply when you have two or more conceptually distinct
sets of variables and want to study their joint or shared structure.

---

## When to use

| Method | Set A | Set B | Goal |
|---|---|---|---|
| CCA | Continuous predictors | Continuous responses | Find linear combinations of A and B that maximally correlate |
| RDA (constrained CCA) | Continuous predictors | Continuous responses | Explain variance in B using A; asymmetric (A explains B) |
| PERMANOVA | Grouping / continuous predictors | Distance matrix from responses | Non-parametric test of group differences in multivariate space |
| Multivariate regression (MANOVA-style) | Categorical ± continuous | Continuous response matrix | Test overall effect of predictors on multiple outcomes jointly |

**CCA vs RDA:**
- CCA maximises correlation between two sets — neither is privileged.
- RDA maximises variance in the response set explained by the predictor set.
  Use RDA when there is a clear predictor / response distinction (RDA ≈ multivariate regression).

**MANOVA vs CCA/RDA:**
- MANOVA is appropriate when predictors are categorical (groups) and you have
  multiple continuous outcomes.
- CCA/RDA are appropriate when both variable sets are continuous or when you want
  to characterise the shared structure, not just test a group difference.

---

## Key decisions to confirm with the user

1. **Set A and Set B** — which variables belong to each set? (For CCA/RDA)
2. **Asymmetry** — is there a causal / predictive direction (→ RDA), or are you
   looking for shared structure without a direction (→ CCA)?
3. **Distance metric** (for PERMANOVA) — Euclidean, Bray-Curtis, Jaccard?
   - Euclidean: continuous, roughly normal variables
   - Bray-Curtis: abundance data, semi-metric
   - Jaccard: binary presence/absence
4. **Number of canonical axes to interpret** — typically retain axes with
   permutation-test p < 0.05, or until cumulative explained variance plateaus.
5. **Covariates to partial out** — partial CCA/RDA removes the effect of a
   covariate set before computing canonical axes.

---

## Model hierarchy

### CCA / RDA hierarchy

```
Level 0 (null):        No predictor constraints — unconstrained ordination (PCA / CA)
Level 1 (covariates):  Partial CCA/RDA partialling out covariates (e.g., site effects)
Level 2 (main model):  CCA/RDA with predictors of interest
```

Compare each level with a permutation F-test (999 permutations minimum).

### PERMANOVA hierarchy

```
Level 0 (null):        Permutation test of group centroid differences, no covariates
Level 1 (covariates):  adonis2(distance ~ site, ...) — partial out site effects
Level 2 (full model):  adonis2(distance ~ site + group + time, ...)
```

---

## R code templates

```r
library(vegan)     # CCA, RDA, PERMANOVA (adonis2)
library(ggplot2)   # plotting
library(ggvegan)   # tidy ggplot for vegan objects (devtools::install_github)

# ── Data preparation ──────────────────────────────────────────────────────────
# Set A (predictors / environment): rows = subjects, cols = variables
env <- df[, c("age", "site", "group", "score")]
env$group <- as.factor(env$group)

# Set B (responses / species / brain measures): numeric matrix
Y   <- df[, c("fa_l_af", "md_l_cst", "vol_hippo")]  # example

# ── RDA (asymmetric: env predicts Y) ─────────────────────────────────────────
# Null: unconstrained PCA
pca_m <- rda(Y)

# Level 1: covariates only (partial RDA)
rda_cov <- rda(Y ~ age + Condition(site), data = env)

# Level 2: full model
rda_m   <- rda(Y ~ age + group + score + Condition(site), data = env)

# Permutation tests
anova(rda_m, permutations = 999)                  # overall model
anova(rda_m, by = "axis", permutations = 999)     # per canonical axis
anova(rda_m, by = "terms", permutations = 999)    # per predictor

# Variance explained
RsquareAdj(rda_m)   # adjusted R²

# Triplot (sites, response variables, predictor vectors)
plot(rda_m, type = "n")
points(rda_m, display = "sites", col = env$group)
text(rda_m, display = "bp", col = "blue")      # predictor arrows
text(rda_m, display = "species", col = "red")  # response variable positions

# ── CCA (symmetric: find shared structure) ────────────────────────────────────
cca_m <- cca(Y ~ age + group + score, data = env)
anova(cca_m, permutations = 999)
anova(cca_m, by = "axis", permutations = 999)

# ── PERMANOVA (distance-based) ────────────────────────────────────────────────
dist_Y <- vegdist(Y, method = "euclidean")  # or "bray", "jaccard"

# Null: overall centroid test
adonis2(dist_Y ~ 1, data = env, permutations = 999)

# Level 1: covariates
adonis2(dist_Y ~ site, data = env, permutations = 999)

# Level 2: full model (sequential SS — order matters)
adonis2(dist_Y ~ site + group + score, data = env,
        permutations = 999, by = "terms")

# Multivariate homogeneity of dispersion (assumption check for PERMANOVA)
bd <- betadisper(dist_Y, env$group)
anova(bd)        # if significant → groups differ in spread, not just centroid
permutest(bd)    # permutation version
```

---

## Python code templates

```python
import numpy as np
from sklearn.cross_decomposition import CCA   # symmetric CCA
import statsmodels.api as sm

# ── CCA via scikit-learn ───────────────────────────────────────────────────────
A = df[["age", "score", "group_coded"]].values    # predictor set
B = df[["fa_l_af", "md_l_cst", "vol_hippo"]].values  # response set

# Standardise both sets
from sklearn.preprocessing import StandardScaler
A = StandardScaler().fit_transform(A)
B = StandardScaler().fit_transform(B)

cca = CCA(n_components=3)   # number of canonical pairs to extract
cca.fit(A, B)
A_c, B_c = cca.transform(A, B)   # canonical variates

# Canonical correlations
for i in range(3):
    r = np.corrcoef(A_c[:, i], B_c[:, i])[0, 1]
    print(f"Canonical correlation {i+1}: {r:.3f}")

# ── PERMANOVA via scikit-bio (pip install scikit-bio) ─────────────────────────
from skbio.stats.distance import permanova, DistanceMatrix
from skbio import DistanceMatrix as DM
from scipy.spatial.distance import pdist, squareform

dist_matrix = squareform(pdist(B, metric="euclidean"))
dm = DM(dist_matrix, df.index.astype(str))
result = permanova(dm, df["group"], permutations=999)
print(result)
```

---

## Julia code templates

```julia
using MultivariateStats, Distances, DataFrames

# CCA
A = Matrix(df[:, [:age, :score]])  # predictor set (n × p)
B = Matrix(df[:, [:fa_l_af, :md_cst]])  # response set (n × q)

# MultivariateStats expects variables as rows
cca = fit(CCA, A', B')
# Canonical correlations
correlations = cca.r
```

---

## Assumption checks

| Method | Assumption | Check |
|---|---|---|
| RDA | Linear relationship between Y and env | Residual plots; consider detrended CA if unimodal relationships |
| RDA | No extreme multicollinearity in env | VIF among predictors (R: `vif.cca()`) |
| CCA | Both sets reasonably continuous | Inspect distributions; avoid binary-dominated sets |
| PERMANOVA | Homogeneity of multivariate dispersion | `betadisper()` + ANOVA; if violated, interpret with caution |
| PERMANOVA | Exchangeability of observations | Satisfied by independent observations or random blocks |

---

## Interpreting outputs

**RDA triplot:**
- **Sites (points):** each observation; proximity = similarity in response space
- **Response variable arrows:** direction of maximum increase in that variable
- **Predictor arrows (biplot scores):** direction of maximum increase in that predictor; arrow length ∝ explanatory power
- **Angle between arrows:** approximate correlation (0° = positive, 180° = negative, 90° = uncorrelated)

**Canonical correlations (CCA):**
- First canonical pair captures the most shared variance; subsequent pairs are orthogonal.
- Report: canonical correlation, percent variance explained per axis, permutation p-value.

**PERMANOVA:**
- Reports R² (proportion of total distance variance explained by the term) and F-statistic.
- Always follow with a `betadisper` test — a significant PERMANOVA result could reflect
  centroid differences (the real effect) or dispersion differences (a confound).

---

## When to escalate

- Latent structure within one variable set → run EFA/PCA first (`factor-analysis.md`),
  then use factor scores as the variable set in CCA/RDA
- Causal pathway hypotheses → SEM (out of scope; suggest dedicated workflow)
- Very high-dimensional response set (p >> n) → mention sparse CCA or PLS (out of scope)
