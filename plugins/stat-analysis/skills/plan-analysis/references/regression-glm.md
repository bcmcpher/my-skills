# Regression and GLM Family

Covers: OLS regression, generalised linear models (logistic, Poisson, negative
binomial, ordinal), linear mixed effects (LME), and generalised linear mixed
models (GLMM). The common thread is a single outcome modelled as a (possibly
transformed) linear combination of predictors.

---

## When to use

| Method | Outcome | Predictors | Design |
|---|---|---|---|
| OLS regression | Continuous, normal residuals | Continuous ± categorical | Independent |
| Logistic regression | Binary (0/1) | Any | Independent |
| Multinomial logistic | Nominal (≥ 3 unordered categories) | Any | Independent |
| Poisson regression | Count (non-negative integers) | Any | Independent |
| Negative binomial | Count, overdispersed | Any | Independent |
| Proportional odds | Ordinal (ranked categories) | Any | Independent |
| LME (`lmer`) | Continuous | Any | Repeated measures / nested |
| GLMM (`glmer`) | Binary, count, or ordinal | Any | Repeated measures / nested |

**OLS vs ANOVA:** These are the same model. Use OLS when at least one key
predictor is continuous; use ANOVA framing when all predictors are categorical.

---

## Key decisions to confirm with the user

1. **Link function / outcome family** — is the outcome continuous (identity link),
   binary (logit), count (log), ordinal (logit for cumulative probabilities)?
2. **Predictors of primary interest vs covariates** — which predictors are the
   hypothesis and which are controls? (determines model hierarchy structure)
3. **Scaling** — should continuous predictors be mean-centred or standardised?
   (standardising gives β in SD units, making coefficients comparable)
4. **Random effects structure** (mixed models only):
   - What is the grouping variable? (subject, site, family)
   - Random intercept only, or also random slopes for within-subject predictors?
   - Start with random intercept only; add slopes only if theory demands it
5. **Reference category** for any categorical predictor

---

## Model hierarchy

```
Level 0 (null):         outcome ~ 1  [+ (1 | group) for mixed]
Level 1 (covariates):   outcome ~ age + site
Level 2 (main effects): outcome ~ age + site + treatment + score
Level 3 (interaction):  outcome ~ age + site + treatment * score
```

Compare adjacent levels with LRT (GLM, GLMM) or F-test (OLS, LME).
See `model-hierarchy.md` for comparison functions and REML notes.

---

## R code templates

```r
library(lme4)
library(lmerTest)   # adds p-values to lmer output
library(MASS)       # negative binomial
library(ordinal)    # proportional odds
library(car)
library(emmeans)

# ── OLS regression ────────────────────────────────────────────────────────────
m0 <- lm(outcome ~ 1,                             data = df)
m1 <- lm(outcome ~ age + site,                    data = df)
m2 <- lm(outcome ~ age + site + group + score,    data = df)
m3 <- lm(outcome ~ age + site + group * score,    data = df)
anova(m0, m1, m2, m3)          # sequential F-tests
car::Anova(m3, type = "III")   # marginal tests for final model

# ── Logistic regression ───────────────────────────────────────────────────────
m0 <- glm(outcome ~ 1,                          family = binomial, data = df)
m1 <- glm(outcome ~ age + site,                 family = binomial, data = df)
m2 <- glm(outcome ~ age + site + group + score, family = binomial, data = df)
anova(m0, m1, test = "LRT")
anova(m1, m2, test = "LRT")
exp(coef(m2))           # odds ratios
exp(confint(m2))        # OR confidence intervals

# ── Poisson regression ────────────────────────────────────────────────────────
m_pois <- glm(count ~ age + group, family = poisson, data = df)
# Check dispersion
dispersion <- sum(residuals(m_pois, type="pearson")^2) / m_pois$df.residual
# If dispersion > 1.5: switch to negative binomial
m_nb <- MASS::glm.nb(count ~ age + group, data = df)
anova(m_pois, test = "LRT")

# ── Proportional odds (ordinal logistic) ──────────────────────────────────────
library(ordinal)
m0 <- clm(ordered(outcome) ~ 1,          data = df)
m1 <- clm(ordered(outcome) ~ age + site, data = df)
m2 <- clm(ordered(outcome) ~ age + site + group, data = df)
anova(m0, m1, m2)   # LRT

# ── Linear mixed effects ───────────────────────────────────────────────────────
# Fit with ML for model comparison, REML for final estimates
m0 <- lmer(outcome ~ 1            + (1 | subject), data = df, REML = FALSE)
m1 <- lmer(outcome ~ age          + (1 | subject), data = df, REML = FALSE)
m2 <- lmer(outcome ~ age + group  + (1 | subject), data = df, REML = FALSE)
m3 <- lmer(outcome ~ age + group + time
                                  + (1 | subject), data = df, REML = FALSE)
# Random slope: allow time effect to vary by subject
m4 <- lmer(outcome ~ age + group + time
                                  + (time | subject), data = df, REML = FALSE)
anova(m0, m1, m2, m3, m4)   # sequential LRT

m_final <- update(m3, REML = TRUE)   # switch to REML for final model
summary(m_final)
car::Anova(m_final, type = "III")

# ICC: proportion of variance at subject level
performance::icc(m_final)

# ── GLMM (binary outcome, repeated measures) ──────────────────────────────────
m0 <- glmer(outcome ~ 1           + (1 | subject), family = binomial, data = df)
m2 <- glmer(outcome ~ group + time + (1 | subject), family = binomial, data = df)
anova(m0, m2)   # LRT
```

---

## Python code templates

```python
import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy import stats

# ── OLS regression ────────────────────────────────────────────────────────────
m0 = smf.ols("outcome ~ 1",                               data=df).fit()
m1 = smf.ols("outcome ~ age + C(site)",                   data=df).fit()
m2 = smf.ols("outcome ~ age + C(site) + C(group) + score", data=df).fit()
m3 = smf.ols("outcome ~ age + C(site) + C(group) * score", data=df).fit()
sm.stats.anova_lm(m0, m1, m2, m3)   # sequential F-table

# ── Logistic regression ───────────────────────────────────────────────────────
m0 = smf.logit("outcome ~ 1",                data=df).fit(disp=False)
m2 = smf.logit("outcome ~ C(group) + score", data=df).fit(disp=False)
# LRT
lr = 2 * (m2.llf - m0.llf)
print(f"LRT χ²={lr:.3f}, p={stats.chi2.sf(lr, df=m2.df_model - m0.df_model):.4f}")
import numpy as np
print("Odds ratios:", np.exp(m2.params))

# ── Poisson regression ────────────────────────────────────────────────────────
m_pois = smf.poisson("count ~ C(group) + age", data=df).fit(disp=False)
dispersion = m_pois.pearson_chi2 / m_pois.df_resid
print(f"Dispersion: {dispersion:.2f}")  # if > 1.5 → use NegBin

# ── Mixed effects ─────────────────────────────────────────────────────────────
m0 = smf.mixedlm("outcome ~ 1",         data=df, groups=df["subject"]).fit()
m2 = smf.mixedlm("outcome ~ group + time", data=df, groups=df["subject"]).fit()
# LRT
lr = 2 * (m2.llf - m0.llf)
print(stats.chi2.sf(lr, df=1))
```

---

## Julia code templates

```julia
using MixedModels, GLM, StatsModels

# OLS
m0 = lm(@formula(outcome ~ 1),                         df)
m2 = lm(@formula(outcome ~ age + group + score),       df)
ftest(m0.model, m2.model)

# Logistic (GLM)
m0 = glm(@formula(outcome ~ 1),     df, Binomial(), LogitLink())
m2 = glm(@formula(outcome ~ group), df, Binomial(), LogitLink())
# LRT: 2*(loglikelihood(m2) - loglikelihood(m0))

# LME
m0 = fit(MixedModel, @formula(outcome ~ 1        + (1|subject)), df)
m2 = fit(MixedModel, @formula(outcome ~ group + time + (1|subject)), df)
MixedModels.lrtest(m0, m2)
```

---

## Assumption checks

### OLS / LME
- **Residual normality:** Q-Q plot and Shapiro-Wilk on residuals (not the raw outcome).
- **Homoscedasticity:** Breusch-Pagan test (`lmtest::bptest()`); plot scale-location.
- **Influential observations:** Cook's distance > 4/N warrants investigation.
- **Independence (LME):** ICC > 0.05 confirms clustering is non-trivial.
- **Random effects normality:** Q-Q plot of BLUPs.

### GLM
- **Logistic:** Hosmer-Lemeshow goodness of fit; ROC curve (AUC-ROC ≥ 0.7 is acceptable).
- **Poisson:** Dispersion check (see above); rootogram for count fit.
- **Proportional odds:** Test of proportional odds assumption (`ordinal::nominal_test()`).

### All models
- VIF for multicollinearity (see `qc-metrics.md`).
- Residuals vs fitted for any systematic trend.

---

## Interpreting coefficients

| Model | Coefficient means |
|---|---|
| OLS | 1-unit increase in X → β-unit change in outcome (holding others constant) |
| Logistic | 1-unit increase in X → exp(β) × odds of outcome = 1 (i.e., OR) |
| Poisson | 1-unit increase in X → exp(β) × rate multiplier |
| Ordinal | 1-unit increase in X → exp(β) × odds of being in higher category |
| LME | Same as OLS for fixed effects; random effects account for clustering |

For standardised predictors (mean 0, SD 1), β is in SD units of the predictor —
coefficients across predictors are directly comparable.

---

## When to escalate

- Multiple correlated outcomes → `anova-family.md` (MANOVA) or `multivariate.md` (CCA)
- Suspected latent predictor structure → `factor-analysis.md`
- Very many predictors (p ≈ n) → mention ridge/LASSO (out of scope)
- Complex causal pathway → suggest SEM (out of scope)
