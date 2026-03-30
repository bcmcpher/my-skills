# ANOVA Family

Covers: one-way ANOVA, factorial ANOVA, ANCOVA, repeated-measures ANOVA,
MANOVA, and MANCOVA. All share the same core assumption: a continuous outcome
explained by categorical predictors (with optional continuous covariates).

---

## When to use

| Method | DV | Predictors | Design |
|---|---|---|---|
| One-way ANOVA | 1 continuous | 1 categorical (≥ 2 groups) | Independent |
| Factorial ANOVA | 1 continuous | 2+ categorical | Independent |
| ANCOVA | 1 continuous | Categorical + ≥ 1 continuous covariate | Independent |
| RM-ANOVA | 1 continuous | ≥ 1 within-subject factor (time, condition) | Repeated measures |
| MANOVA | ≥ 2 continuous | Categorical | Independent |
| MANCOVA | ≥ 2 continuous | Categorical + covariate(s) | Independent |

**When NOT to use ANOVA — escalate to LME instead:**
- Unbalanced repeated measures with missing time points
- More than 2–3 levels of a within-subject factor (sphericity assumption is fragile)
- Subjects nested in a higher-level clustering variable (sites, schools)

---

## Key decisions to confirm with the user

1. **Reference category** for each factor — which group is coded as the baseline?
   (affects contrast interpretation, not overall test)
2. **Within-subject factors** — which predictors are measured on the same subject
   (determines whether to use RM-ANOVA or a between-subject factor)
3. **Type of SS** — Type I (sequential, order-dependent) or Type III (marginal,
   appropriate for unbalanced designs and designs with interactions)? Default: Type III.
4. **MANOVA follow-up** — if the omnibus MANOVA is significant, do they want
   univariate ANOVAs per DV, or discriminant function analysis?

---

## Model hierarchy

```
Level 0 (null):         outcome ~ 1
Level 1 (covariates):   outcome ~ age + site
Level 2 (main effects): outcome ~ age + site + group + condition
Level 3 (interaction):  outcome ~ age + site + group * condition
```

For MANOVA, replace scalar `outcome` with a response matrix `cbind(dv1, dv2, ...)`.

---

## R code templates

```r
library(car)      # Type III ANOVA
library(emmeans)  # post-hoc contrasts
library(lme4)     # for RM-ANOVA via LME

# ── One-way ANOVA ─────────────────────────────────────────────────────────────
m0 <- lm(outcome ~ 1,     data = df)
m1 <- lm(outcome ~ group, data = df)
anova(m0, m1)                         # overall F
car::Anova(m1, type = "III")          # Type III SS
emmeans(m1, ~ group) |> pairs(adjust = "tukey")  # post-hoc

# ── Factorial ANOVA ───────────────────────────────────────────────────────────
m0 <- lm(outcome ~ 1,              data = df)
m1 <- lm(outcome ~ group,          data = df)
m2 <- lm(outcome ~ group + cond,   data = df)
m3 <- lm(outcome ~ group * cond,   data = df)
anova(m0, m1, m2, m3)
car::Anova(m3, type = "III")
emmeans(m3, ~ group | cond) |> pairs(adjust = "tukey")  # simple effects

# ── ANCOVA ────────────────────────────────────────────────────────────────────
m0 <- lm(outcome ~ age,             data = df)   # covariate-only baseline
m1 <- lm(outcome ~ age + group,     data = df)
m2 <- lm(outcome ~ age * group,     data = df)   # test homogeneity of slopes
anova(m0, m1)  # group effect after controlling for age
# If age * group is NS, drop interaction and use m1 as final model

# ── Repeated-measures ANOVA via LME ───────────────────────────────────────────
# Recommended over aov() — handles missing data and unbalanced designs
library(lmerTest)
m0 <- lmer(outcome ~ 1    + (1 | subject), data = df, REML = FALSE)
m1 <- lmer(outcome ~ time + (1 | subject), data = df, REML = FALSE)
m2 <- lmer(outcome ~ time * group + (1 | subject), data = df, REML = FALSE)
anova(m0, m1, m2)
# Refit with REML=TRUE for final estimates
m_final <- lmer(outcome ~ time * group + (1 | subject), data = df, REML = TRUE)
summary(m_final)

# ── MANOVA ────────────────────────────────────────────────────────────────────
Y  <- cbind(df$dv1, df$dv2, df$dv3)   # response matrix
m0 <- manova(Y ~ 1,     data = df)
m1 <- manova(Y ~ group, data = df)
anova(m0, m1)
summary(m1, test = "Pillai")    # Pillai's trace (robust to assumption violations)
summary(m1, test = "Wilks")     # Wilks' lambda (most powerful when assumptions hold)
# Follow-up univariate ANOVAs (with correction)
summary.aov(m1)

# ── MANCOVA ───────────────────────────────────────────────────────────────────
m1 <- manova(Y ~ age + group, data = df)
summary(m1, test = "Pillai")
```

---

## Python code templates

```python
import statsmodels.formula.api as smf
import statsmodels.api as sm
from statsmodels.multivariate.manova import MANOVA
import pingouin as pg   # pip install pingouin — cleaner RM-ANOVA

# ── One-way ANOVA ─────────────────────────────────────────────────────────────
m = smf.ols("outcome ~ C(group)", data=df).fit()
sm.stats.anova_lm(m, typ=3)

# ── Factorial ANOVA ───────────────────────────────────────────────────────────
m = smf.ols("outcome ~ C(group) * C(condition)", data=df).fit()
sm.stats.anova_lm(m, typ=3)

# ── ANCOVA ────────────────────────────────────────────────────────────────────
m = smf.ols("outcome ~ age + C(group)", data=df).fit()
sm.stats.anova_lm(m, typ=3)

# ── Repeated-measures ANOVA (via pingouin) ────────────────────────────────────
pg.rm_anova(data=df, dv="outcome", within="time", subject="subject")
pg.mixed_anova(data=df, dv="outcome", within="time", between="group", subject="subject")

# ── MANOVA ────────────────────────────────────────────────────────────────────
mv = MANOVA.from_formula("dv1 + dv2 + dv3 ~ group", data=df)
print(mv.mv_test())
```

---

## Assumption checks (see qc-metrics.md for full detail)

| Assumption | Test / Plot | Violation remedy |
|---|---|---|
| Normality of residuals | Q-Q plot, Shapiro-Wilk on residuals | Transform DV; use robust ANOVA (R: `WRS2`) |
| Homogeneity of variance | Levene's test | Welch's ANOVA (`oneway.test(var.equal=FALSE)`) |
| Sphericity (RM-ANOVA) | Mauchly's test | Apply Greenhouse-Geisser or Huynh-Feldt correction |
| Homogeneity of covariance matrices (MANOVA) | Box's M test | Use Pillai's trace (more robust than Wilks) |
| Homogeneity of regression slopes (ANCOVA) | Interaction term (covariate × group) NS | If significant: use Johnson-Neyman or stratify |
| Independence | Design knowledge | LME for clustered/nested data |

---

## Effect sizes

```r
library(effectsize)
eta_squared(car::Anova(m, type = "III"))    # η²
omega_squared(car::Anova(m, type = "III"))  # ω² (less biased)
cohens_d(outcome ~ group, data = df)        # for two-group contrasts
```

---

## Post-hoc contrasts

Always specify contrasts before seeing the data if possible (planned contrasts
need no correction). For unplanned post-hoc:

```r
emm <- emmeans(model, ~ group)         # marginal means
pairs(emm, adjust = "tukey")           # all pairwise, Tukey correction
contrast(emm, method = "trt.vs.ctrl")  # vs reference group only (Dunnett)
```

---

## When to escalate

- Subjects nested in sites or families → `regression-glm.md` (LME with cluster random effect)
- Outcome is binary, count, or ordinal → `regression-glm.md` (GLMM)
- Outcomes share latent structure → `factor-analysis.md` (EFA/CFA) before MANOVA
- Need to model a causal path or mediation → suggest SEM (out of scope)
