# Worked Examples: Regression Analysis

Annotated workflows for common regression patterns. Each example traces the
full decision path — from intake through model hierarchy, QC checks, and
result reporting. Source: graduate regression course (Psyc 650/790) assignments
and lab materials, translated to R / Python / Julia. SAS code is not reproduced.

---

## Table of contents

1. [Simple regression — reporting workflow](#1-simple-regression)
2. [Two-predictor regression — partial and semi-partial correlations](#2-two-predictor-regression)
3. [Hierarchical regression — incremental R² and set tests](#3-hierarchical-regression)
4. [Curvilinear regression — polynomial terms and mean centering](#4-curvilinear-regression)
5. [Categorical predictors — dummy, effect, and contrast coding](#5-categorical-predictors)
6. [Interaction regression — simple slopes at ±1 SD](#6-interaction-regression)

---

## 1. Simple regression

**Research question:** Does SAT score predict college GPA?

**Intake:**
- Outcome: continuous (GPA)
- Predictor: continuous (SAT)
- Design: independent observations, N = 250
- Decision tree path: continuous outcome → continuous predictor → OLS regression

**Model hierarchy:**

```
Level 0 (null):   GPA ~ 1
Level 1 (model):  GPA ~ SAT
```

### Step 0 — EDA before fitting

Always produce a scatterplot with a linear fit line and a loess smoother
overlaid. If the loess line departs from the linear line beyond sampling noise,
consider a polynomial term (see Example 4).

```r
# R
library(ggplot2)
ggplot(df, aes(x = SAT, y = GPA)) +
  geom_point(alpha = 0.4) +
  geom_smooth(method = "lm",   se = TRUE, colour = "steelblue", linetype = "solid") +
  geom_smooth(method = "loess", se = FALSE, colour = "tomato",   linetype = "dashed") +
  labs(title = "GPA ~ SAT: linear fit vs. loess smoother")
```

```python
# Python
import matplotlib.pyplot as plt
import numpy as np
from statsmodels.nonparametric.smoothers_lowess import lowess

fig, ax = plt.subplots()
ax.scatter(df["SAT"], df["GPA"], alpha=0.4)
# Linear fit line
m_line = np.polyfit(df["SAT"], df["GPA"], 1)
x_grid = np.linspace(df["SAT"].min(), df["SAT"].max(), 200)
ax.plot(x_grid, np.polyval(m_line, x_grid), color="steelblue", label="OLS")
# Loess smoother
smoothed = lowess(df["GPA"], df["SAT"], frac=0.5)
ax.plot(smoothed[:, 0], smoothed[:, 1], color="tomato", linestyle="--", label="loess")
ax.legend(); ax.set_xlabel("SAT"); ax.set_ylabel("GPA")
```

### Step 1 — Descriptives and correlation

```r
# R
library(psych)
describe(df[c("SAT", "GPA")])    # mean, SD, skewness, kurtosis
cor(df$SAT, df$GPA, use = "complete.obs")
```

```python
# Python
import pandas as pd
from scipy import stats
print(df[["SAT", "GPA"]].describe())
print("skewness:", df[["SAT", "GPA"]].skew())
print("kurtosis:", df[["SAT", "GPA"]].kurt())
r, p = stats.pearsonr(df["SAT"].dropna(), df["GPA"].dropna())
print(f"r = {r:.3f}, p = {p:.4f}")
```

### Step 2 — Fit models and compare

```r
# R
m0 <- lm(GPA ~ 1,   data = df)
m1 <- lm(GPA ~ SAT, data = df)
anova(m0, m1)          # F-test: does SAT explain significant variance?
summary(m1)            # coefficient table: β, SE, t, p
confint(m1, level = 0.95)
```

```python
# Python
import statsmodels.formula.api as smf
m0 = smf.ols("GPA ~ 1",   data=df).fit()
m1 = smf.ols("GPA ~ SAT", data=df).fit()
print(m1.summary())
# Sequential F-test
import statsmodels.api as sm
sm.stats.anova_lm(m0, m1)
```

```julia
# Julia
using GLM, DataFrames, StatsModels
m0 = lm(@formula(GPA ~ 1),   df)
m1 = lm(@formula(GPA ~ SAT), df)
ftest(m0.model, m1.model)
println(coeftable(m1))
```

### Step 3 — Extract and report from ANOVA table

The ANOVA table partitions total variance (SS_Y) into model variance (SS_reg)
and residual variance (SS_res). Always compute and report these quantities.

```
R²     = SS_reg / SS_Y                  — proportion of variance explained
F      = (SS_reg / df_reg) / (SS_res / df_res)
       = MS_reg / MS_res
df_reg = number of predictors (p = 1 here)
df_res = N - p - 1
RMSE   = √MS_res                        — "error of estimation" (SD of residuals)
```

```r
# R — extract all quantities from lm summary
s <- summary(m1)
r_sq  <- s$r.squared
adj_r <- s$adj.r.squared
f_val <- s$fstatistic[1]
f_df  <- s$fstatistic[2:3]
rmse  <- s$sigma

cat(sprintf("R² = %.4f, adj-R² = %.4f\n", r_sq, adj_r))
cat(sprintf("F(%d, %d) = %.2f\n", f_df[1], f_df[2], f_val))
cat(sprintf("RMSE (error of estimation) = %.4f\n", rmse))

# Coefficient table with 95% CI
coeff_table <- cbind(coef(m1), confint(m1))
colnames(coeff_table) <- c("B", "95% CI low", "95% CI high")
print(round(coeff_table, 4))
```

```python
# Python
m = m1
print(f"R²={m.rsquared:.4f}, adj-R²={m.rsquared_adj:.4f}")
print(f"F({int(m.df_model)},{int(m.df_resid)}) = {m.fvalue:.2f}, p = {m.f_pvalue:.4f}")
print(f"RMSE = {m.mse_resid**0.5:.4f}")
print(m.conf_int())
```

### Step 4 — Standardised regression coefficient

The standardised coefficient β* is the raw slope expressed in SD units of both
variables. It equals Pearson r for a single predictor. Two ways to get it:

```r
# R — method 1: scale both variables first
df$GPA_z  <- scale(df$GPA)
df$SAT_z  <- scale(df$SAT)
m1_std <- lm(GPA_z ~ SAT_z, data = df)
coef(m1_std)["SAT_z"]   # β* — identical to r

# R — method 2: lm.beta from QuantPsyc or effectsize
library(effectsize)
standardize_parameters(m1)  # adds Std_Coefficient column
```

```python
# Python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
df_z = pd.DataFrame(
    scaler.fit_transform(df[["SAT", "GPA"]]), columns=["SAT_z", "GPA_z"]
)
m1_std = smf.ols("GPA_z ~ SAT_z", data=df_z).fit()
print("β* =", m1_std.params["SAT_z"])   # equals Pearson r
```

**Interpretation rule:**
- Raw β: "a 1-unit increase in SAT is associated with a β-unit increase in GPA"
- Standardised β*: "a 1-SD increase in SAT is associated with a β*-SD increase in GPA"
- The two are related: β* = β × (SD_X / SD_Y)

### Step 5 — Mean centering

Centering shifts X so that 0 means "at the mean," not "at the true zero."
**The slope (β₁) does not change. Only the intercept changes.**

```r
# R
df$SAT_c <- df$SAT - mean(df$SAT, na.rm = TRUE)
m1_c <- lm(GPA ~ SAT_c, data = df)
summary(m1_c)
# Intercept is now the predicted GPA at mean SAT (more interpretable)
# Slope is unchanged
```

```python
# Python
df["SAT_c"] = df["SAT"] - df["SAT"].mean()
m1_c = smf.ols("GPA ~ SAT_c", data=df).fit()
print(m1_c.params)
```

**When to centre:** Always centre continuous predictors when they are part of a
polynomial or interaction term (see Examples 4 and 6). Centering for a simple
linear model is optional but makes the intercept substantively meaningful.

---

## 2. Two-predictor regression

**Research question:** Does GPA depend on both SAT score and previous achievement (Prevach)?

**Additional concepts introduced:** partial regression coefficients, partial and
semi-partial correlations, tolerance (multicollinearity).

### Partial vs semi-partial correlations

```
Partial correlation of X1 and Y:   correlation of Y and X1 after removing X2 from BOTH
Semi-partial correlation of X1:    correlation between Y (whole) and X1 (with X2 removed)
sr²                                unique variance in Y explained by X1 alone (not shared with X2)
```

```r
# R
library(ppcor)
m2 <- lm(GPA ~ SAT + Prevach, data = df)
summary(m2)

# Partial and semi-partial correlations for all predictors
spcor(df[c("GPA", "SAT", "Prevach")])    # semi-partial
pcor(df[c("GPA", "SAT", "Prevach")])     # partial

# Or extract from model
library(effectsize)
standardize_parameters(m2)    # standardised betas
```

```python
# Python
import pingouin as pg
m2 = smf.ols("GPA ~ SAT + Prevach", data=df).fit()
print(m2.summary())

# Semi-partial (part) correlations: use pingouin
result = pg.partial_corr(data=df, x="SAT", y="GPA", covar="Prevach")
print(result)   # partial r of SAT controlling for Prevach
```

### Multicollinearity: Tolerance

```
Tolerance of X1 = 1 - R²(X1 ~ all other Xs)
             = proportion of variance in X1 not shared with other predictors

VIF = 1 / Tolerance

Rules of thumb:
  Tolerance < 0.10  →  possible collinearity problem
  VIF > 10          →  strong collinearity; standard errors are inflated
```

```r
# R
library(car)
vif(m2)          # VIF for each predictor
1 / vif(m2)      # tolerance

# Or manually for a two-predictor model
m_x1 <- lm(SAT ~ Prevach, data = df)
tol_SAT <- 1 - summary(m_x1)$r.squared
cat("Tolerance of SAT:", round(tol_SAT, 4))
```

```python
# Python
from statsmodels.stats.outliers_influence import variance_inflation_factor

X = sm.add_constant(df[["SAT", "Prevach"]])
vif_df = pd.DataFrame({
    "variable": ["SAT", "Prevach"],
    "VIF": [variance_inflation_factor(X.values, i+1) for i in range(2)],
})
vif_df["tolerance"] = 1 / vif_df["VIF"]
print(vif_df)
```

```julia
# Julia — manual tolerance
using GLM, DataFrames
m_x1 = lm(@formula(SAT ~ Prevach), df)
tol_SAT = 1 - r2(m_x1)
println("Tolerance of SAT: ", round(tol_SAT, digits=4))
```

---

## 3. Hierarchical regression

**Research question:** What proportion of variance in mammogram intention (INTENT1)
is explained by (1) medical input, (2) breast disease history, and (3) health
belief constructs? Does each set add significant predictive power beyond the
previous?

Source: Aiken, West, Woodward & Reno (1994, Health Psychology 13(2), 122-129)
Variables: HAVEPHYS, PHYSREC (medical input); LUMP, WOMREL (history);
SUSCEPT1, SEVERE1, BENEFIT1, BARRIER1 (health beliefs); INTENT1 (criterion)

**Key concept — ΔR² (R² change):**

Each block adds a set of predictors to the previous model. The incremental R²
(ΔR²) is how much new variance the block explains. The F-test for ΔR² tests
whether that increment is greater than chance.

```
ΔR² = R²(full model) - R²(reduced model)

F_change = (ΔR² / k) / ((1 - R²_full) / (N - p_full - 1))

where k = number of predictors added in this block
      p_full = total predictors in full model
```

### R

```r
library(lm)

m1 <- lm(INTENT1 ~ HAVEPHYS + PHYSREC,
         data = df)
m2 <- lm(INTENT1 ~ HAVEPHYS + PHYSREC + LUMP + WOMREL,
         data = df)
m3 <- lm(INTENT1 ~ HAVEPHYS + PHYSREC + LUMP + WOMREL +
                   SUSCEPT1 + SEVERE1 + BENEFIT1 + BARRIER1,
         data = df)

# Sequential F-tests for each increment
anova(m1, m2, m3)

# R² at each step
lapply(list(m1, m2, m3), function(m) {
  s <- summary(m)
  c(R2 = s$r.squared, adj_R2 = s$adj.r.squared)
})

# Report: for each model step, state
#   R² for this model
#   ΔR² = R² - R²(previous)
#   F for ΔR², df, p
#   Which individual predictors in the new block are significant

# Example output format:
# Block 1 (medical input): R² = .08, F(2, N-3) = x.xx, p = .xxx
# Block 2 (history): ΔR² = .04, F(2, N-5) = x.xx, p = .xxx
# Block 3 (beliefs): ΔR² = .15, F(4, N-9) = x.xx, p = .xxx
```

### Python

```python
import statsmodels.formula.api as smf
import statsmodels.api as sm

m1 = smf.ols("INTENT1 ~ HAVEPHYS + PHYSREC", data=df).fit()
m2 = smf.ols("INTENT1 ~ HAVEPHYS + PHYSREC + LUMP + WOMREL", data=df).fit()
m3 = smf.ols("INTENT1 ~ HAVEPHYS + PHYSREC + LUMP + WOMREL"
             " + SUSCEPT1 + SEVERE1 + BENEFIT1 + BARRIER1", data=df).fit()

# Sequential ANOVA table
print(sm.stats.anova_lm(m1, m2, m3))
# Columns: df_resid, ssr (SS_res), df_diff, ss_diff, F, Pr(>F)

# Extract R² at each step
for label, m in [("Block 1", m1), ("Block 2", m2), ("Block 3", m3)]:
    print(f"{label}: R²={m.rsquared:.4f}, adj-R²={m.rsquared_adj:.4f}")
```

### Julia

```julia
using GLM, DataFrames, StatsModels

m1 = lm(@formula(INTENT1 ~ HAVEPHYS + PHYSREC), df)
m2 = lm(@formula(INTENT1 ~ HAVEPHYS + PHYSREC + LUMP + WOMREL), df)
m3 = lm(@formula(INTENT1 ~ HAVEPHYS + PHYSREC + LUMP + WOMREL +
                            SUSCEPT1 + SEVERE1 + BENEFIT1 + BARRIER1), df)

# Sequential F-tests
ftest(m1.model, m2.model)
ftest(m2.model, m3.model)

# R² at each step
for (label, m) in [("Block 1", m1), ("Block 2", m2), ("Block 3", m3)]
    println("$label: R² = $(round(r2(m), digits=4))")
end
```

### What to check and report at each step

1. **R² for each model** — cumulative explained variance
2. **ΔR²** — unique contribution of each block; compute as difference of R² values
3. **F for ΔR²** — from the `anova()` comparison; report df₁ (predictors added) and df₂ (residual)
4. **Significance of individual predictors in the new block** — t-tests and p-values from `summary()`
5. **Note:** a significant overall F for a block does not guarantee any individual predictor is significant (one predictor may be carrying the block)

---

## 4. Curvilinear regression

**Research question:** Does the number of course credits predict elective interest
in a curved (non-linear) relationship?

**Key principle:** Always centre the predictor before computing polynomial terms.
Failing to centre inflates collinearity between X and X² to the point of
numerical instability. The quadratic coefficient β₂ and the omnibus fit statistics
are unchanged by centering; only the intercept and β₁ change.

```
Centred model:   Y = β₀ + β₁(X - X̄) + β₂(X - X̄)² + ε
```

### Fitting the polynomial hierarchy

```r
# R
df$Xc   <- df$X - mean(df$X)
df$Xc2  <- df$Xc^2
df$Xc3  <- df$Xc^3   # only if testing cubic

m_lin   <- lm(Y ~ Xc,         data = df)
m_quad  <- lm(Y ~ Xc + Xc2,   data = df)
m_cubic <- lm(Y ~ Xc + Xc2 + Xc3, data = df)
anova(m_lin, m_quad, m_cubic)   # is each higher-order term justified?

summary(m_quad)
# If Xc2 is significant: the quadratic term improves fit
# β₁ at the centred point = derivative of the curve at X̄; sign shows direction of slope at mean
# β₂ > 0: upward parabola (U-shaped); β₂ < 0: downward parabola (inverted U)
```

```python
# Python
import numpy as np
df["Xc"]  = df["X"] - df["X"].mean()
df["Xc2"] = df["Xc"] ** 2

m_lin  = smf.ols("Y ~ Xc",       data=df).fit()
m_quad = smf.ols("Y ~ Xc + Xc2", data=df).fit()

print(sm.stats.anova_lm(m_lin, m_quad))   # is quadratic term significant?
print(m_quad.summary())
print(f"ΔR² (quadratic gain) = {m_quad.rsquared - m_lin.rsquared:.4f}")
```

```julia
# Julia
df.Xc  = df.X .- mean(df.X)
df.Xc2 = df.Xc .^ 2

m_lin  = lm(@formula(Y ~ Xc),       df)
m_quad = lm(@formula(Y ~ Xc + Xc2), df)
ftest(m_lin.model, m_quad.model)   # F-test for quadratic gain
println("ΔR² = ", round(r2(m_quad) - r2(m_lin), digits=4))
```

### Multicollinearity check for polynomial terms

Uncentred polynomial predictors (X and X²) are nearly perfectly correlated.
Centred versions (Xc and Xc²) are not.

```r
# R — check tolerance before and after centering
library(car)
# Without centering (BAD)
m_raw <- lm(Y ~ X + I(X^2), data = df)
vif(m_raw)    # expect VIF >> 10

# With centering (GOOD)
vif(m_quad)   # expect VIF close to 1
```

### Interpreting the coefficients (centred polynomial)

```
β₀  = predicted Y when X = X̄  (i.e., at the vertex, roughly)
β₁  = slope of Y at X = X̄ (first derivative at the mean)
β₂  = curvature; rate at which the slope changes per unit of X
      β₂ > 0 → rate of increase is accelerating (U-shape)
      β₂ < 0 → rate of increase is decelerating (inverted-U)

Rule: if the quadratic term is significant, the lower-order term (Xc) must remain
in the model regardless of its own significance. Dropping Xc would constrain the
vertex to be at X = 0, which is almost never theoretically justified.
```

### Plot the fitted curve

```r
# R
library(ggplot2)
df$fitted_quad <- fitted(m_quad)
ggplot(df, aes(x = Xc, y = Y)) +
  geom_point(alpha = 0.4) +
  geom_line(aes(y = fitted_quad), colour = "steelblue", linewidth = 1.2) +
  labs(title = "Quadratic fit (centred X)")
```

```python
# Python
x_grid = np.linspace(df["Xc"].min(), df["Xc"].max(), 200)
y_grid = m_quad.params["Intercept"] + m_quad.params["Xc"] * x_grid + m_quad.params["Xc2"] * x_grid**2
plt.scatter(df["Xc"], df["Y"], alpha=0.4)
plt.plot(x_grid, y_grid, color="steelblue", linewidth=2, label="quadratic fit")
plt.xlabel("Xc"); plt.ylabel("Y"); plt.legend()
```

---

## 5. Categorical predictors

**Research question:** Do political party affiliations (Republican, Democrat,
Independent) predict attitudes toward marijuana legalization?

**Three coding approaches** for a k-level factor (here k = 3):

| Coding | Reference | Intercept meaning | Slope meaning |
|--------|-----------|-------------------|---------------|
| Dummy  | One group = 0 | Predicted Y for reference group | Difference from reference group |
| Effect | Unweighted mean | Grand mean of group means | Deviation from grand mean |
| Contrast | User-defined | Grand mean (weighted) | Specific directional comparison |

### Dummy coding (R = reference group)

```r
# R — relevel to set reference group
df$Party <- factor(df$Party, levels = c("Republican", "Democrat", "Independent"))
# df$Party is now treatment-coded (dummy) with Republican = 0

m_dummy <- lm(Marijuana ~ Party, data = df)
summary(m_dummy)
# Intercept = mean for Republicans
# PartyDemocrat = Democrat - Republican mean difference
# PartyIndependent = Independent - Republican mean difference
```

```python
# Python — C(Party, Treatment('Republican')) for explicit reference
m_dummy = smf.ols("Marijuana ~ C(Party, Treatment(reference='Republican'))",
                  data=df).fit()
print(m_dummy.summary())
```

```julia
# Julia — set reference via categorical contrast
using CategoricalArrays
df.Party = categorical(df.Party; levels=["Republican", "Democrat", "Independent"])
m_dummy = lm(@formula(Marijuana ~ Party), df)
coeftable(m_dummy)
```

### Effect coding (deviation from unweighted grand mean)

```r
# R — sum-to-zero (effect) coding
contrasts(df$Party) <- contr.sum(3)
m_effect <- lm(Marijuana ~ Party, data = df)
summary(m_effect)
# Intercept = unweighted mean of the three group means (grand mean of means)
# Party1 = Republican deviation from grand mean
# Party2 = Democrat deviation from grand mean
# (Independent deviation = -(Party1 + Party2))
```

```python
# Python — sum coding via formulaic / pandas
from pandas.api.types import CategoricalDtype
# Manually construct sum-coded dummies
df["E1"] = df["Party"].map({"Republican": 1,  "Democrat": 0, "Independent": -1})
df["E2"] = df["Party"].map({"Republican": 0,  "Democrat": 1, "Independent": -1})
m_effect = smf.ols("Marijuana ~ E1 + E2", data=df).fit()
print(m_effect.summary())
```

### Contrast coding (theory-driven comparisons)

Use when the hypothesis specifies a particular ordering or grouping.
Example: Democrat and Independent are expected to be more liberal than Republican.

```r
# R — contrast: {Rep} vs {Dem + Ind}, then {Dem} vs {Ind}
cmat <- matrix(c(-2,  1,  1,    # contrast 1: Rep vs (Dem+Ind)/2
                  0,  1, -1),   # contrast 2: Dem vs Ind
               nrow = 2, byrow = TRUE)
contrasts(df$Party) <- t(cmat)
m_contrast <- lm(Marijuana ~ Party, data = df)
summary(m_contrast)
# Party1: tests whether Rep differs from average of Dem+Ind
# Party2: tests whether Dem differs from Ind
```

**Note:** R² is identical across dummy, effect, and contrast coding for the same
factor. Only the interpretation of the intercept and slopes changes.

---

## 6. Interaction regression

**Research question:** Does the effect of predictor X on Y depend on the level
of a second continuous predictor Z?

**Principle:** Centre both X and Z before forming the crossproduct. Centring is
mandatory, not optional: without it, the main effects (β₁, β₂) are conditional
at X = 0 or Z = 0 (meaningless for most scales), and X and XZ are highly
collinear.

**Equation:**
```
Ŷ = β₀ + β₁(X - X̄) + β₂(Z - Z̄) + β₃(X - X̄)(Z - Z̄)
```

### Fitting the interaction model

```r
# R
df$Xc  <- df$X - mean(df$X)
df$Zc  <- df$Z - mean(df$Z)
df$XZc <- df$Xc * df$Zc

m_int <- lm(Y ~ Xc + Zc + XZc, data = df)
summary(m_int)
# β₃ tests the interaction: is the XZc coefficient significant?
# β₁ is the effect of X at the mean of Z
# β₂ is the effect of Z at the mean of X
```

```python
# Python
df["Xc"]  = df["X"] - df["X"].mean()
df["Zc"]  = df["Z"] - df["Z"].mean()
df["XZc"] = df["Xc"] * df["Zc"]

m_int = smf.ols("Y ~ Xc + Zc + XZc", data=df).fit()
print(m_int.summary())
```

```julia
# Julia
df.Xc  = df.X .- mean(df.X)
df.Zc  = df.Z .- mean(df.Z)
df.XZc = df.Xc .* df.Zc

m_int = lm(@formula(Y ~ Xc + Zc + XZc), df)
coeftable(m_int)
```

### Simple slopes analysis

If β₃ is significant, follow up with simple slopes: the regression of Y on X
at Z = Z̄ + SD_Z (high Z), Z = Z̄ (mean Z), and Z = Z̄ - SD_Z (low Z).

**Algebraically:** at a given value z₀ of Z, the simple regression of Y on X is:
```
Ŷ = (β₀ + β₂ z₀) + (β₁ + β₃ z₀) X
                         ↑
         this is the simple slope of Y on X at z₀
```

```r
# R — three simple slope equations by hand
sd_Z <- sd(df$Zc)
b0   <- coef(m_int)["(Intercept)"]
b1   <- coef(m_int)["Xc"]
b2   <- coef(m_int)["Zc"]
b3   <- coef(m_int)["XZc"]

ss_high <- b1 + b3 *  sd_Z   # simple slope at Z = +1 SD
ss_mean <- b1                 # simple slope at Z = mean
ss_low  <- b1 + b3 * -sd_Z   # simple slope at Z = -1 SD

cat(sprintf("Simple slopes: high Z = %.4f, mean Z = %.4f, low Z = %.4f\n",
            ss_high, ss_mean, ss_low))

# R — test each simple slope with emmeans or by re-parametrising
# Re-parametrisation: shift Z so that zero = +1 SD, then test β₁ in new model
df$Z_high  <- df$Zc - sd_Z      # zero of new variable = +1 SD above mean
df$XZ_high <- df$Xc * df$Z_high
m_high <- lm(Y ~ Xc + Z_high + XZ_high, data = df)
summary(m_high)  # Xc coefficient = simple slope at Z = mean + 1 SD; its t-test is the simple slope test
```

```python
# Python
import numpy as np

sd_Z = df["Zc"].std()
b1, b3 = m_int.params["Xc"], m_int.params["XZc"]

for label, z0 in [("Z = +1 SD", sd_Z), ("Z = mean", 0), ("Z = -1 SD", -sd_Z)]:
    ss = b1 + b3 * z0
    print(f"{label}: simple slope = {ss:.4f}")

# Test via re-parametrisation
df["Z_high"]  = df["Zc"] - sd_Z
df["XZ_high"] = df["Xc"] * df["Z_high"]
m_high = smf.ols("Y ~ Xc + Z_high + XZ_high", data=df).fit()
print(m_high.summary().tables[1])   # Xc row = simple slope test at +1 SD
```

```julia
# Julia
sd_Z = std(df.Zc)
b1, b3 = coef(m_int)[2], coef(m_int)[4]  # Xc, XZc

for (label, z0) in [("Z = +1 SD", sd_Z), ("Z = mean", 0.0), ("Z = -1 SD", -sd_Z)]
    ss = b1 + b3 * z0
    println("$label: simple slope = $(round(ss, digits=4))")
end
```

### Plot the three simple regression lines

```r
# R
library(ggplot2)
sd_Z <- sd(df$Zc)
x_grid <- seq(min(df$Xc), max(df$Xc), length.out = 100)

pred_fun <- function(z0) {
  (b0 + b2 * z0) + (b1 + b3 * z0) * x_grid
}

plot_df <- data.frame(
  Xc    = rep(x_grid, 3),
  Yhat  = c(pred_fun(sd_Z), pred_fun(0), pred_fun(-sd_Z)),
  Z_level = rep(c("+1 SD", "Mean", "-1 SD"), each = 100)
)
ggplot(plot_df, aes(x = Xc, y = Yhat, colour = Z_level)) +
  geom_line(linewidth = 1.2) +
  labs(x = "X (centred)", y = "Predicted Y", colour = "Z level",
       title = "Simple regression lines at three levels of Z")
```

```python
# Python
import matplotlib.pyplot as plt

b0_val = m_int.params["Intercept"]
x_grid = np.linspace(df["Xc"].min(), df["Xc"].max(), 100)
fig, ax = plt.subplots()
for label, z0, col in [("+1 SD", sd_Z, "steelblue"), ("Mean", 0, "black"), ("-1 SD", -sd_Z, "tomato")]:
    y_hat = (b0_val + b2 * z0) + (b1 + b3 * z0) * x_grid
    ax.plot(x_grid, y_hat, color=col, label=f"Z = {label}", linewidth=2)
ax.set_xlabel("X (centred)"); ax.set_ylabel("Predicted Y"); ax.legend()
```

### Interpretation guidelines

```
β₃ is significant (interaction term):
  → The effect of X on Y depends on Z (or equivalently, the effect of Z on Y
    depends on X). Describe the interaction by reporting and plotting simple
    slopes — not by interpreting β₁ and β₂ in isolation.

β₁ and β₂ in the interaction model:
  → These are conditional effects at the mean of the other predictor (because
    both are centred). They do NOT represent the main effect of X or Z averaged
    across all values of the other variable; use them only to interpret the
    effect "at the mean."

β₃ is not significant:
  → Retain the additive model (Xc + Zc, no crossproduct). The interaction
    model has one more parameter and a higher threshold for generalisation.
```
