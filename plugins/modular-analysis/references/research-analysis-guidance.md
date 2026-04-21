# Research analysis scripting guidance

Draft reference for refining `analysis-plan` and `analysis-refactor`.

This document describes where guidance for **research analysis scripts** should intentionally
diverge from default software-engineering advice for packages, libraries, and applications.
The goal is not to excuse sloppy code. The goal is to optimize for a different primary
outcome: **a transparent, reproducible scientific record that collaborators can audit,
modify, and rerun**.

---

## Core principle

When writing a research analysis, ask:

> Will this make it easier for a future collaborator to understand what scientific
> decisions were made, in what order, and how to reproduce the results?

If the answer is yes, prefer it — even when the result is slightly less abstract,
less DRY, or less "package-like" than conventional programming guidance would suggest.

---

## What changes in research analysis mode

In general programming, code is often optimized for reuse across many contexts, minimal
duplication, and abstraction boundaries that hide implementation details.

In research analysis, the code is often serving three roles at once:

1. It is an executable workflow.
2. It is documentation of scientific decisions.
3. It is a record of how a result was produced.

That means some ordinary best practices change in emphasis.

| Topic | General programming default | Research analysis default |
|---|---|---|
| Primary goal | Reuse, maintainability, extensibility | Reproducibility, auditability, scientific clarity |
| Comments | Sparse; explain only non-obvious code | Frequent when they explain rationale, design choices, exclusions, assumptions |
| Control flow | Abstract repeated logic into helpers early | Keep a readable top-to-bottom narrative unless abstraction clearly improves auditability |
| DRY | Eliminate repetition aggressively | Allow small, local repetition when it keeps analytical logic explicit |
| Configuration | Centralize and generalize for reuse | Surface study-specific choices so they are easy to inspect and edit |
| APIs/helpers | Hide implementation details behind clean interfaces | Keep important scientific choices visible, even if that means thinner abstractions |
| Intermediates | Avoid unnecessary outputs and temporary artifacts | Save important intermediate outputs when they help reproducibility or review |
| Naming | Prefer concise technical names consistent with codebase conventions | Prefer domain names that collaborators will immediately recognize |

---

## 1. Write the script as an analytical narrative

For a novel analysis, the file should usually read in the same order that a researcher
would explain the workflow to a colleague:

1. State assumptions and fixed choices.
2. Load data.
3. Apply global cleaning and exclusions.
4. Derive variables.
5. Run models or computations.
6. Summarize outputs.
7. Save artifacts.

This is often better than immediately pushing logic into a deeply layered architecture.

### Prefer

- Clear section headers marking each stage of the analysis.
- Short comments that explain why a transformation exists.
- A mostly linear flow in the main script, with helpers extracted only where they remove
  real complexity or repeated units of work.

### Avoid

- Refactoring the analysis into a package-style architecture so early that a reader must
  jump across many files to understand one result.
- Hiding the scientific procedure behind generic helper names like `process()`,
  `run_pipeline()`, or `execute_step()`.
- Breaking the analysis into many tiny helpers whose only effect is to obscure order.

### Example: better for research analysis

```python
# Restrict to baseline visits because the primary hypothesis concerns
# cross-sectional association at study entry, not longitudinal change.
baseline = data.loc[data["visit"] == "baseline"].copy()

# Exclude participants without both imaging and clinical data so that
# the regression and descriptive tables use the same analytic sample.
baseline = baseline.dropna(subset=["fa", "updrs_total", "age", "sex"])

# Standardize FA for effect-size comparability across tracts.
baseline["fa_z"] = (baseline["fa"] - baseline["fa"].mean()) / baseline["fa"].std()
```

### Example: worse for research analysis

```python
df = process_inputs(load_and_filter(get_data()))
```

The second version may be concise, but it hides which exclusions were applied, why they
were applied, and whether the transformations match the intended scientific question.

---

## 2. Use comments to explain scientific reasoning, not just mechanics

In package code, comments that restate the code are noise. In analysis scripts,
comments that explain **scientific rationale** are often essential.

### Good comment types in a research script

- Why a cohort restriction exists.
- Why one covariate set was chosen over another.
- Why a transformation or threshold is scientifically justified.
- What an intermediate object represents conceptually.
- What is exploratory versus confirmatory.

### Weak comment types

- Comments that just narrate syntax.
- Comments copied from old analyses that no longer match the code.
- Vague claims like "clean data" without specifying what was changed.

### Do

```r
# Use complete cases for this model because the manuscript reports a single
# sample size per outcome and we want the fitted model and exported table to
# describe the same participants.
model_df <- subset_df |>
  dplyr::filter(complete.cases(updrs_total, fa, age, sex, site))
```

### Do not

```r
# Filter complete cases
model_df <- subset_df |>
  dplyr::filter(complete.cases(updrs_total, fa, age, sex, site))
```

The second comment names the operation but not the reason. The first comment records a
scientific and reporting choice that a future collaborator may need to defend.

---

## 3. Prefer explicitness over maximal DRY

General programming often treats repetition as a smell to remove immediately.
Research analysis requires a more selective rule:

> Remove repetition when it obscures a repeated unit of work. Keep repetition when
> removing it would hide a methodological choice.

### Appropriate repetition in research analysis

- A short block repeated for two pre-registered sensitivity analyses.
- Separate model formulas written out explicitly when they represent distinct scientific
  specifications.
- A couple of named intermediate tables saved separately because each corresponds to a
  figure or table in the manuscript.

### Inappropriate repetition

- Copy-pasting the same analysis across 20 outcomes when the only change is outcome name.
- Repeating the same export logic for every metric instead of using one helper.
- Duplicating data cleaning steps in multiple places so samples silently diverge.

### Better to keep explicit

```python
primary_formula = "updrs_total ~ fa_z + age + sex + site"
sensitivity_formula = "updrs_total ~ fa_z + age + sex + site + disease_duration"
```

These are different scientific models. Keeping them explicit helps review.

### Better to abstract

```python
for outcome in OUTCOMES:
    run_one(data, tract="fa", outcome=outcome, formula=PRIMARY_FORMULA)
```

If the only thing changing is the outcome, a loop is clearer and safer than copy-paste.

### Do not over-abstract

```python
specs = build_specs_from_registry(CONFIG, MODE, FLAGS)
execute(specs, strategy="standard")
```

This may be fine in production software, but it is often too indirect for a one-off
analysis where a reviewer needs to see exactly what model was run.

---

## 4. Keep scientific choices visible and near the top

A research script should make major design choices easy to inspect without reading deep
into function bodies.

These often include:

- outcomes, predictors, ROIs, contrasts, cohorts
- inclusion/exclusion rules
- covariates
- thresholds
- seeds
- input datasets
- output directories
- model formulas

### Do

```python
ANALYSIS_NAME = "baseline_fa_updrs"
INPUT_PATH = "derived/merged_baseline.csv"
OUTPUT_DIR = "results/baseline_fa_updrs"

OUTCOMES = ["updrs_total", "updrs_motor"]
COVARIATES = ["age", "sex", "site"]
MIN_COMPLETE_CASES = 30
RANDOM_SEED = 20260421
```

### Do not

```python
def fit_model(df, outcome):
    covariates = ["age", "sex", "site"]
    min_cases = 30
    np.random.seed(20260421)
    ...
```

In general programming, localizing details can reduce global clutter. In a research
analysis, burying methodological choices inside helpers makes them harder to audit.

---

## 5. Save intermediates when they improve reproducibility

In application code, extra intermediate outputs can look wasteful.
In research analysis, they can be part of the reproducible record.

Useful intermediate artifacts include:

- the cleaned analysis dataset
- per-outcome complete-case tables
- model coefficient tables before post-processing
- QC summaries
- subject inclusion/exclusion logs

### Good practice

```python
cleaned.to_csv(f"{OUTPUT_DIR}/analysis_dataset.csv", index=False)
sample_sizes.to_csv(f"{OUTPUT_DIR}/sample_sizes.csv", index=False)
coef_table.to_csv(f"{OUTPUT_DIR}/fa_updrs_total_coefficients.csv", index=False)
```

### Poor practice

- Recomputing everything from raw data with no saved checkpoint.
- Saving only the final figure, with no table showing what sample or model produced it.
- Overwriting intermediate outputs without stable names or metadata.

### Important constraint

Do not save intermediates indiscriminately. Save them when they help someone verify:

1. what data entered the model,
2. what exclusions occurred,
3. what output corresponds to which run.

---

## 6. Prefer domain-readable names over generic engineering names

Package code often favors concise internal names that fit local conventions.
Analysis scripts should favor names that a domain collaborator can recognize quickly.

### Prefer

- `baseline_complete_cases`
- `motor_outcomes`
- `tract_summary`
- `primary_model_table`
- `eligible_subjects`

### Avoid

- `tmp2`
- `processed`
- `result_obj`
- `final_data`
- `run_step`

### Contrast with general programming

In a library, a generic helper like `normalize_inputs()` may be fine because the caller
knows the domain context already. In a research script, a name like
`standardize_fa_within_site()` is often better because it reveals exactly what happened.

---

## 7. Use simple control flow and predictable order

Research analyses are often reviewed by people who are not expert programmers.
Prefer straightforward loops, explicit conditionals, and obvious sequencing.

### Prefer

```python
for tract in TRACTS:
    for outcome in OUTCOMES:
        run_one(data, tract, outcome, config)
```

### Avoid when unnecessary

```python
list(
    map(
        lambda pair: run_one(data, pair[0], pair[1], config),
        itertools.product(TRACTS, OUTCOMES),
    )
)
```

The second version is not wrong, but the first is easier to read, annotate, and debug.

### Another example

Prefer a few explicit `if` branches over compact one-liners when each branch corresponds
to a substantive analytical decision.

---

## 8. Distinguish reusable utilities from study-specific logic

Not every analysis script should become a package. But not every script should remain
entirely monolithic either.

Use this rule:

- Extract **reusable mechanics** into helpers.
- Keep **study-specific reasoning** visible in the analysis script.

### Good candidates for helper functions

- loading a standardized file format
- applying the same complete-case rule repeatedly
- formatting coefficient tables
- saving plots with consistent dimensions
- fitting the same model family across outcomes

### Better left visible in the script

- why baseline was chosen instead of follow-up
- which covariate set is primary versus sensitivity
- why one subgroup was excluded
- why a threshold was selected
- how outputs map to manuscript figures/tables

### Good split

```python
def coefficient_table(model):
    return ...

# Primary model for the manuscript: baseline FA predicting total UPDRS,
# adjusted for age, sex, and site.
model = fit_linear_model(model_df, formula=PRIMARY_FORMULA)
table = coefficient_table(model)
```

This keeps the reusable table-formatting helper, while the script still documents the
scientific meaning of the model being fit.

---

## 9. Make exploratory choices explicit

Research code often evolves during discovery. That is normal. What matters is whether the
script clearly distinguishes:

- pre-specified analyses
- sensitivity analyses
- exploratory follow-ups

### Do

```python
# Exploratory follow-up: site-stratified models requested after inspecting
# heterogeneity in the pooled estimates. These are not part of the primary analysis.
for site in SITES:
    ...
```

### Do not

- Mix exploratory and primary analyses into one undifferentiated loop.
- Reuse output filenames such that exploratory results overwrite primary outputs.
- Present post hoc thresholds or filters as if they were original design choices.

General programming advice rarely emphasizes this because software usually does not need
to encode the epistemic status of a computation. Research analysis often does.

---

## 10. Be explicit about failure, skipping, and exclusions

One major reproducibility risk is silent loss of data or silently skipped runs.

### Do

- log when rows are excluded and why
- log when a tract/outcome pair is skipped
- save sample sizes per analysis unit
- raise or record informative errors for degenerate cases

### Example

```python
if subset.shape[0] < MIN_COMPLETE_CASES:
    raise ValueError(
        f"{tract}/{outcome}: only {subset.shape[0]} complete cases; "
        f"need at least {MIN_COMPLETE_CASES}"
    )
```

### Do not

```python
if len(subset) < 30:
    return None
```

The second version may be acceptable in internal code if the caller handles it carefully.
In a research script, it is too easy for this to become a silent omission from final
results.

---

## 11. Favor deterministic behavior over convenience

Research analyses should be reproducible across reruns whenever possible.

### Do

- set seeds explicitly
- sort outputs deterministically
- specify factor/order levels explicitly
- define column selections explicitly
- use stable output paths

### Do not

- rely on ambient global state
- depend on nondeterministic row order
- let filenames be created from ad hoc string concatenation in multiple places
- use hidden defaults when an explicit option exists

### Contrast

In a production system, convenience defaults may be acceptable if behavior is well tested.
In research analysis, explicit settings usually win because they reduce ambiguity about
what was actually run.

---

## 12. Do not optimize prematurely for hypothetical reuse

General software advice often says to design for extensibility. For a novel analysis, this
can become counterproductive if it leads to speculative abstraction.

### Signs of over-engineering in a research script

- introducing class hierarchies for a one-off workflow
- adding plugin/registry systems before there are real variants to manage
- pushing all parameters into nested config objects that obscure core choices
- creating helpers with generic names before repeated usage exists

### Better approach

Start with:

1. a readable analysis script,
2. a clear `run_one()` for the repeated unit,
3. a few well-chosen helpers,
4. explicit constants and outputs.

Only generalize further when:

- the same pattern is reused across multiple analyses,
- collaborators repeatedly need the same helper,
- abstraction clearly reduces mistakes without hiding reasoning.

---

## A practical decision rule for coding agents

When deciding whether to refactor a research analysis toward more abstraction, ask:

1. Does this make the scientific procedure easier to follow?
2. Does this keep methodological choices visible?
3. Does this improve reproducibility or auditability?
4. Would a domain collaborator find the new version easier to inspect?

If the answer to these is no, do not apply the abstraction just because it would be a
good idea in ordinary software engineering.

---

## Short do / don't summary

### Do

- write the analysis in a readable scientific order
- comment the rationale for exclusions, thresholds, and model choices
- keep fixed scientific choices visible
- use explicit, domain-readable names
- save meaningful intermediate artifacts
- log exclusions, failures, and sample sizes
- extract helpers only when they simplify repeated mechanics without hiding reasoning

### Don't

- over-abstract early
- remove comments that explain methodological intent
- hide model specifications inside generic helpers
- silently skip failed units of work
- bury thresholds and covariate choices deep in functions
- optimize for hypothetical future reuse at the cost of present-day clarity

---

## Candidate wording for plugin incorporation

Use this mode when the user is writing a **novel research analysis** rather than a
general-purpose software component. In this mode, optimize for reproducibility,
auditability, and scientific readability. Prefer a mostly linear script with strong
sectioning and comments that explain the rationale for exclusions, transformations,
covariates, thresholds, and output structure. Extract helpers when they clarify a repeated
unit of work, but do not aggressively abstract away methodological choices or force the
analysis into package-style architecture if that would make the scientific logic harder to
inspect.
