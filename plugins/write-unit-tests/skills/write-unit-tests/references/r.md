# R Testing Reference

## Framework: testthat

`testthat` is the standard R testing framework. Check `DESCRIPTION` for `Suggests: testthat`
or look for a `tests/testthat/` directory.

## Test file location

- `tests/testthat/test-<module>.R`
- Run from the package root (assumes R package structure)
- For scripts (non-package), place `test-<script>.R` alongside the source

## Running tests

```r
# Inside an R session
library(testthat)
test_file("tests/testthat/test-mymodule.R")   # single file
test_dir("tests/testthat/")                   # all tests
devtools::test()                               # package-level (preferred)
```

```bash
# From the shell
Rscript -e "testthat::test_file('tests/testthat/test-mymodule.R')"
Rscript -e "devtools::test()"
```

## AI-generated marker

R doesn't have a built-in decorator system. Place `# AI-Generated` directly above each
`test_that()` block:

```r
library(testthat)

# AI-Generated
test_that("add returns correct sum for positive numbers", {
  expect_equal(add(2, 3), 5)
})

# AI-Generated
test_that("add raises error for non-numeric input", {
  expect_error(add("a", 1))
})
```

## Test structure patterns

### Basic expectations

```r
# AI-Generated
test_that("divide returns correct quotient", {
  expect_equal(divide(10, 2), 5)
  expect_equal(divide(-6, 2), -3)
})

# AI-Generated
test_that("divide errors on zero divisor", {
  expect_error(divide(1, 0))
})

# AI-Generated
test_that("parse_date returns NA for invalid string", {
  expect_true(is.na(parse_date("not-a-date")))
})
```

### Common expectation functions

```r
expect_equal(result, expected)         # equality (with tolerance for floats)
expect_identical(result, expected)     # strict equality (same type)
expect_error(expr, regexp)             # errors with optional message pattern
expect_warning(expr, regexp)           # warnings
expect_message(expr, regexp)           # messages
expect_true(condition)
expect_false(condition)
expect_null(result)
expect_length(result, n)
expect_s3_class(result, "data.frame") # class check
```

### Float comparisons

```r
# AI-Generated
test_that("area calculation is approximately correct", {
  expect_equal(circle_area(1), pi, tolerance = 1e-6)
})
```

### Testing with fixtures (local helper data)

```r
# Define at the top of the test file
sample_df <- data.frame(x = c(1, 2, 3), y = c(4, 5, 6))

# AI-Generated
test_that("summarize_data returns correct mean", {
  result <- summarize_data(sample_df)
  expect_equal(result$mean_x, 2)
})
```

## Expected failures (source bugs)

Use `expect_failure()` or `skip()` with a comment:

```r
# AI-Generated — skipped: Bug in float rounding, see GitHub issue #7
test_that("handles float edge case", {
  skip("Bug: rounding error in divide() — see issue #7")
  expect_equal(divide(1.0, 3.0) * 3, 1.0)
})
```
