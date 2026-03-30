# Decision Tree: Outcome × Predictors × Design → Method

Navigate this tree top-down using the answers from the four intake questions.
Each leaf names the recommended method family and the reference file to load.

---

## Branch 1: No explicit outcome (structure discovery)

The user wants to understand the latent structure of a variable set, reduce
dimensionality, or find groupings — not predict a specific outcome.

| Goal | Variables | → Method | Reference |
|---|---|---|---|
| Find latent factors underlying continuous variables | All continuous | EFA → CFA if confirming | `factor-analysis.md` |
| Reduce dimensionality, no latent variable model needed | All continuous | PCA | `factor-analysis.md` |
| Find clusters or latent classes | Continuous or categorical | k-means / LCA | out of scope — name it |
| Find shared structure between two variable sets | Two continuous sets | CCA | `multivariate.md` |

---

## Branch 2: Single continuous outcome

### 2a: Predictors are categorical only (groups, conditions)

| Design | → Method | Reference |
|---|---|---|
| Independent observations, one grouping factor | One-way ANOVA | `anova-family.md` |
| Independent observations, two+ grouping factors | Factorial ANOVA | `anova-family.md` |
| Independent observations, ANOVA + continuous covariate(s) | ANCOVA | `anova-family.md` |
| Each subject measured at multiple time points or conditions | RM-ANOVA or LME | `anova-family.md` |
| Subjects nested in sites, families, or schools | LME (random intercept for cluster) | `regression-glm.md` |

### 2b: Predictors include continuous variables (with or without categorical)

| Design | → Method | Reference |
|---|---|---|
| Independent observations, all continuous predictors | OLS regression | `regression-glm.md` |
| Independent observations, continuous + categorical predictors | OLS with factors (ANCOVA-style) | `regression-glm.md` |
| Repeated measures or longitudinal | Linear mixed effects (LME / `lmer`) | `regression-glm.md` |
| Subjects nested in clusters | LME with random intercepts | `regression-glm.md` |
| Many predictors, small N (p ≈ n or p > n) | Ridge / LASSO — out of scope; flag this | — |

**Deciding factor between ANOVA and regression when both seem plausible:**
- All predictors categorical → ANOVA family (conceptually cleaner, standard in experimental psychology/neuroscience)
- At least one continuous predictor of primary interest → regression family
- Both are equivalent for balanced designs; regression is more general

---

## Branch 3: Single binary outcome (yes/no, case/control, pass/fail)

| Design | → Method | Reference |
|---|---|---|
| Independent observations | Logistic regression | `regression-glm.md` |
| Repeated measures or nested | GLMM with binomial family | `regression-glm.md` |
| Purely categorical predictors, large N | Chi-squared / log-linear (mention) | `regression-glm.md` |

---

## Branch 4: Single count or rate outcome

| Design | → Method | Reference |
|---|---|---|
| Independent observations, no overdispersion | Poisson regression | `regression-glm.md` |
| Independent observations, overdispersed counts | Negative binomial regression | `regression-glm.md` |
| Repeated measures or nested | GLMM with Poisson / NegBin family | `regression-glm.md` |

**Overdispersion check:** fit Poisson, compute dispersion = residual deviance / df.
If > 1.5, switch to negative binomial.

---

## Branch 5: Single ordinal outcome (ranked scale, Likert with few levels)

| Design | → Method | Reference |
|---|---|---|
| Independent observations | Proportional odds (ordinal logistic) | `regression-glm.md` |
| Repeated measures | GLMM with ordinal family (R: `ordinal::clmm`) | `regression-glm.md` |

**When to treat ordinal as continuous:** Likert scales with 7+ levels and
approximately symmetric distributions are often analysed with OLS in practice —
flag this as a pragmatic choice and document the assumption.

---

## Branch 6: Multiple continuous outcomes

| Structure | Goal | → Method | Reference |
|---|---|---|---|
| Categorical predictors, outcomes share a common cause | Test group differences across all outcomes simultaneously | MANOVA / MANCOVA | `anova-family.md` |
| Continuous predictors + multiple outcomes | Multivariate regression or MANCOVA | `anova-family.md` |
| Two distinct variable sets; want to find their shared variance | Canonical correlation | CCA in `multivariate.md` |
| Multiple outcomes with community/ecological distance matrix | Non-parametric multivariate test | PERMANOVA in `multivariate.md` |
| Outcomes may share latent structure | EFA / CFA first, then SEM if path model needed | `factor-analysis.md` |

**Key question to ask:** "Are your multiple outcomes measurements of the same
underlying construct, or are they conceptually independent?" The answer separates
MANOVA (independent outcomes, test jointly) from factor analysis (outcomes as
indicators of a latent variable).

---

## Branch 7: Ambiguous or complex designs — flags to raise

These signals in the user's description require a clarifying question before routing:

| Signal | Question to ask | Implication |
|---|---|---|
| "before and after" / "pre/post" | Is the same subject measured twice? | Paired t-test → RM-ANOVA → LME |
| "nested" / "clustered" / "multi-site" | What is nested in what? | Random effects for the cluster variable |
| "time series" / "longitudinal" | How many time points? Fixed or varying? | LME or GEE; not repeated-measures ANOVA |
| "brain regions" / "ROIs" as DVs | Are you testing each region separately or jointly? | Multiple testing correction vs MANOVA/CCA |
| "mediator" / "pathway" / "indirect effect" | Is there a hypothesised causal pathway? | Out of scope; suggest SEM / mediation analysis |
| Very small N (< 20 per group) | Will power support the planned model complexity? | Reduce parameters; consider non-parametric |
| Highly skewed or zero-inflated outcome | Does a normal residual assumption hold? | GLM / transformation / non-parametric |
