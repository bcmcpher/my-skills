# R Patterns

Shared utility code for R-based statistical analysis workflows. Load this file
when you need import blocks, model comparison helpers, or diagnostic plot wrappers.
Avoids re-implementing these in every generated script.

---

## Standard library block

```r
library(lme4)        # mixed effects: lmer, glmer
library(lmerTest)    # p-values for lmer via Satterthwaite ddf
library(car)         # Type III ANOVA: Anova()
library(emmeans)     # estimated marginal means and contrasts
library(effectsize)  # eta_squared, omega_squared, cohens_d
library(performance) # icc(), r2()
library(ggplot2)
library(ggfortify)   # autoplot() for lm/glm/lmer objects
library(patchwork)   # combine ggplot panels with + and /
```

---

## Model comparison helpers

### Sequential model comparison (wraps anova())

```r
compare_models <- function(..., test = "F") {
  # Convenience wrapper: runs anova() on a list of models and prints
  # a clean table. For GLMs use test="LRT"; for lmer use test="Chisq".
  models <- list(...)
  tbl <- anova(models[[1]], models[[2]], test = test)
  if (length(models) > 2) {
    for (i in seq(3, length(models))) {
      tbl <- rbind(tbl, anova(models[[i-1]], models[[i]], test = test)[2, ])
    }
  }
  print(tbl)
  invisible(tbl)
}
```

---

## Diagnostic plot wrappers

### 4-panel diagnostic plot

```r
plot_diagnostics <- function(model, title = NULL) {
  # Works for lm, glm, and lmer objects via ggfortify::autoplot().
  # For lmer, ggfortify falls back to base residual/QQ plots.
  p <- ggfortify::autoplot(model, which = 1:4, ncol = 2,
                           label.size = 3, alpha = 0.5)
  if (!is.null(title)) p <- p + patchwork::plot_annotation(title = title)
  print(p)
  invisible(p)
}
```

### Caterpillar plot (random intercepts — LME)

```r
plot_caterpillar <- function(model, group_var = NULL) {
  # Dotplot of random intercept BLUPs +/- 95% CI.
  # Sorts subjects by estimated intercept so outliers are easy to spot.
  re <- lme4::ranef(model, condVar = TRUE)
  lattice::dotplot(re, scales = list(x = list(relation = "free")),
                   main = "Random effects (BLUPs +/- 95% CI)")
}
```

---

## Effect size and reporting helper

```r
report_effects <- function(model, type = "III") {
  # Prints Type III ANOVA table alongside eta-sq and omega-sq effect sizes.
  aov_tbl   <- car::Anova(model, type = type)
  eta_tbl   <- effectsize::eta_squared(aov_tbl, partial = TRUE)
  omega_tbl <- effectsize::omega_squared(aov_tbl, partial = TRUE)
  cat("\n-- Type III ANOVA --\n");   print(aov_tbl)
  cat("\n-- Effect sizes --\n")
  print(cbind(eta_tbl[, c("Parameter", "Eta2_partial")],
              Omega2_partial = omega_tbl$Omega2_partial))
  invisible(list(anova = aov_tbl, eta = eta_tbl, omega = omega_tbl))
}
```

---

## Post-hoc contrasts template

```r
# Estimated marginal means + all pairwise comparisons (Tukey correction)
emm   <- emmeans::emmeans(model, ~ group)
pairs(emm, adjust = "tukey")

# Vs reference group only (Dunnett correction)
contrast(emm, method = "trt.vs.ctrl")

# Simple effects for an interaction
emm2 <- emmeans::emmeans(model, ~ group | condition)
pairs(emm2, adjust = "tukey")
```
