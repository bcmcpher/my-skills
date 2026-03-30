# Julia Patterns

Shared utility code for Julia-based statistical analysis workflows. Julia coverage
is thinner than R and Python across this plugin — for full code templates and
diagnostics, consult `r-patterns.md` or `python-patterns.md` and translate idioms.
The patterns below cover the most common model-fitting and comparison tasks.

---

## Standard using block

```julia
using DataFrames, CSV, XLSX          # data I/O
using GLM, MixedModels               # regression and mixed effects
using StatsModels, StatsBase         # formula syntax, summary stats
using HypothesisTests                # chi-squared, F-tests
using MultivariateStats              # PCA, CCA
using CategoricalArrays              # categorical columns
using Plots, StatsPlots              # plotting (GR backend default)
```

---

## Model comparison helpers

### Sequential LRT for mixed effects models

```julia
"""
lrtest_sequential(models...)

Run pairwise likelihood ratio tests on a sequence of MixedModels, printing
chi-sq, df, and p-value for each adjacent pair.
"""
function lrtest_sequential(models...)
    for i in 2:length(models)
        m0, m1 = models[i-1], models[i]
        stat = 2 * (loglikelihood(m1) - loglikelihood(m0))
        df   = dof(m1) - dof(m0)
        p    = ccdf(Chisq(df), stat)
        println("Step $i: χ²($df) = $(round(stat, digits=3)), p = $(round(p, digits=4))")
    end
end
```

### F-test for OLS models

```julia
# Nested OLS F-test: compare m0 (restricted) to m1 (full)
using GLM
ftest(m0.model, m1.model)   # returns FTestResult with F, df, p
```

---

## Residual diagnostics (basic)

```julia
using StatsPlots

function plot_residuals(model; title="Residual Diagnostics")
    fitted_vals = predict(model)
    resids      = residuals(model)

    p1 = scatter(fitted_vals, resids; xlabel="Fitted", ylabel="Residuals",
                 title="Residuals vs Fitted", legend=false, alpha=0.5)
    hline!(p1, [0]; color=:red, linewidth=0.8)

    p2 = qqnorm(resids; title="Normal Q-Q", qqline=:fit)

    plot(p1, p2; layout=(1, 2), suptitle=title)
end
```

---

## Notes on Julia coverage

- `MixedModels.jl` is production-quality; prefer it over `GLM.jl` for random effects.
- `MultivariateStats.jl` supports PCA and CCA but lacks `vegan`-style permutation
  tests — for PERMANOVA, use Python (`skbio`) or R (`vegan`).
- `Turing.jl` / `Turing` ecosystem for Bayesian models is out of scope here.
- Factor analysis (`EFA`, `CFA`) has no mature Julia package as of early 2025;
  use R (`psych`, `lavaan`) for those workflows.
