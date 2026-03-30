# Model Hierarchy: Null → Full

The purpose of a hierarchical model sequence is to attribute explained variance
to specific terms incrementally, so each step answers a testable question. Every
sequence starts at the null model, regardless of method family.

---

## The four levels

| Level | Contains | Tests |
|---|---|---|
| 0 — Null | Intercept only (grand mean / baseline rate) | Nothing; establishes the floor |
| 1 — Covariates | Confounds and demographic controls only | Does any covariation exist at all? |
| 2 — Main effects | Predictors of primary interest (+ covariates) | Do the key predictors explain outcome beyond covariates? |
| 3 — Interactions | Product terms among primary predictors | Does the effect of one predictor depend on another? |

Add further levels for polynomial terms, three-way interactions, or nested
structures as needed. The principle remains the same: each level adds exactly one
conceptual question.

---

## Comparison tests between levels

| Model family | Comparison test | Function |
|---|---|---|
| OLS / ANOVA | F-test (incremental) | R: `anova(m0, m1)`; Python: `sm.stats.anova_lm(m0, m1)` |
| GLM (logistic, Poisson) | Likelihood ratio test (LRT) | R: `anova(m0, m1, test="LRT")`; Python: `scipy.stats.chi2.sf(2*(ll1-ll0), df=Δp)` |
| Mixed effects (LME/GLMM) | LRT (REML=FALSE for fixed effects) | R: `anova(m0, m1)` on models fit with `REML=FALSE` |
| MANOVA | Pillai's trace / Wilks' lambda | R: `anova(m0, m1)` on `manova` objects |
| CCA | Permutation F-test | R: `anova(cca_model, permutations=999)` |

**REML note for LME:** Always refit with `REML=FALSE` (ML estimation) when
comparing fixed-effect structures. Use REML only for the final model to obtain
unbiased variance estimates.

---

## R code patterns

```r
library(lme4)       # mixed effects
library(lmerTest)   # p-values for lmer
library(car)        # Type III ANOVA
library(emmeans)    # estimated marginal means

# ── OLS / ANOVA family ────────────────────────────────────────────────────────
m0 <- lm(outcome ~ 1,                          data = df)
m1 <- lm(outcome ~ age + site,                 data = df)   # covariates
m2 <- lm(outcome ~ age + site + group + score, data = df)   # main effects
m3 <- lm(outcome ~ age + site + group * score, data = df)   # interaction

anova(m0, m1)   # F-test: do covariates explain anything?
anova(m1, m2)   # F-test: do main effects add beyond covariates?
anova(m2, m3)   # F-test: does the interaction add beyond main effects?

car::Anova(m3, type = "III")  # Type III SS for unbalanced designs

# ── Linear mixed effects ───────────────────────────────────────────────────────
m0 <- lmer(outcome ~ 1              + (1 | subject), data = df, REML = FALSE)
m1 <- lmer(outcome ~ age + site     + (1 | subject), data = df, REML = FALSE)
m2 <- lmer(outcome ~ age + site + group + time
                                    + (1 | subject), data = df, REML = FALSE)
m3 <- lmer(outcome ~ age + site + group * time
                                    + (1 | subject), data = df, REML = FALSE)

anova(m0, m1, m2, m3)  # sequential LRT table

# Refit final model with REML for inference
m_final <- lmer(outcome ~ age + site + group * time + (1 | subject),
                data = df, REML = TRUE)
summary(m_final)

# ── GLM family ────────────────────────────────────────────────────────────────
m0 <- glm(outcome ~ 1,                          family = binomial, data = df)
m1 <- glm(outcome ~ age + site,                 family = binomial, data = df)
m2 <- glm(outcome ~ age + site + group + score, family = binomial, data = df)
m3 <- glm(outcome ~ age + site + group * score, family = binomial, data = df)

anova(m0, m1, test = "LRT")
anova(m1, m2, test = "LRT")
anova(m2, m3, test = "LRT")

# ── GLMM ──────────────────────────────────────────────────────────────────────
m0 <- glmer(outcome ~ 1              + (1 | subject), family = binomial, data = df)
m2 <- glmer(outcome ~ group + time   + (1 | subject), family = binomial, data = df)
anova(m0, m2)  # LRT
```

---

## Python code patterns

```python
import statsmodels.formula.api as smf
import statsmodels.api as sm
from scipy import stats

# ── OLS ───────────────────────────────────────────────────────────────────────
m0 = smf.ols("outcome ~ 1",                            data=df).fit()
m1 = smf.ols("outcome ~ age + C(site)",                data=df).fit()
m2 = smf.ols("outcome ~ age + C(site) + C(group) + score", data=df).fit()
m3 = smf.ols("outcome ~ age + C(site) + C(group) * score", data=df).fit()

# Incremental F-test (manual)
def f_test(restricted, full):
    rss_r = restricted.ssr; rss_f = full.ssr
    df_r  = restricted.df_resid; df_f = full.df_resid
    F = ((rss_r - rss_f) / (df_r - df_f)) / (rss_f / df_f)
    p = stats.f.sf(F, df_r - df_f, df_f)
    return F, p

# LRT for GLMs
def lrt(restricted, full):
    stat = 2 * (full.llf - restricted.llf)
    df   = full.df_model - restricted.df_model
    return stat, stats.chi2.sf(stat, df)

# ── GLM: logistic ────────────────────────────────────────────────────────────
m0 = smf.logit("outcome ~ 1",           data=df).fit(disp=False)
m2 = smf.logit("outcome ~ C(group) + score", data=df).fit(disp=False)
print(lrt(m0, m2))

# ── Mixed effects (via statsmodels MixedLM) ───────────────────────────────────
m0 = smf.mixedlm("outcome ~ 1",         data=df, groups=df["subject"]).fit()
m2 = smf.mixedlm("outcome ~ group + time", data=df, groups=df["subject"]).fit()
print(lrt(m0, m2))
```

---

## Julia code patterns

```julia
using MixedModels, GLM, StatsModels, HypothesisTests

# ── OLS ───────────────────────────────────────────────────────────────────────
m0 = lm(@formula(outcome ~ 1),                    df)
m1 = lm(@formula(outcome ~ age + site),           df)
m2 = lm(@formula(outcome ~ age + site + group + score), df)
m3 = lm(@formula(outcome ~ age + site + group & score), df)

ftest(m0.model, m1.model, m2.model, m3.model)  # sequential F-tests

# ── Linear mixed effects ───────────────────────────────────────────────────────
m0 = fit(MixedModel, @formula(outcome ~ 1        + (1|subject)), df)
m2 = fit(MixedModel, @formula(outcome ~ group + time + (1|subject)), df)
MixedModels.lrtest(m0, m2)   # LRT

# ── GLM (logistic) ────────────────────────────────────────────────────────────
m0 = glm(@formula(outcome ~ 1),      df, Binomial(), LogitLink())
m2 = glm(@formula(outcome ~ group),  df, Binomial(), LogitLink())
# LRT manually: 2*(loglikelihood(m2) - loglikelihood(m0))
```

---

## Model comparison metrics

Use these when comparing non-nested models or selecting among several candidates:

| Metric | Penalises | Lower is better | When to use |
|---|---|---|---|
| AIC | Number of parameters (lightly) | Yes | General model selection |
| BIC | Number of parameters (heavily, log-N) | Yes | When parsimony is prioritised |
| Adjusted R² | Model complexity (for OLS) | No (higher better) | OLS only, descriptive |
| LOOIC / WAIC | (Bayesian; out of scope here) | — | — |

AIC and BIC are not substitutes for LRT when models are nested — use both.
AIC/BIC differences < 2 are not meaningful; > 10 is strong evidence.

---

## Degrees of freedom and sample size guidance

| Model type | Minimum N per estimated parameter |
|---|---|
| OLS | 10–20 observations per predictor |
| Logistic regression | 10–20 events per predictor (EPV rule) |
| Mixed effects (random intercept) | ≥ 20 groups; ≥ 5 observations per group |
| MANOVA | N > (number of DVs + number of predictors) per cell |
| CCA | N > 3 × (p + q) where p, q = number of variables in each set |

Flag to the user if their sample size falls below these thresholds.
