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

Place `# AI-Generated` directly above each `test_that()` block:

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

### Arrange / Act / Assert

```r
# AI-Generated
test_that("divide returns correct quotient", {
  # Arrange
  numerator <- 10
  denominator <- 2

  # Act
  result <- divide(numerator, denominator)

  # Assert
  expect_equal(result, 5)
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
  # Arrange
  input <- sample_df

  # Act
  result <- summarize_data(input)

  # Assert
  expect_equal(result$mean_x, 2)
})
```

## Dependency isolation (mocking)

Unit tests should not call real external services, read real files, or depend on
network state. Use the `mockery` package for mocking in R.

### Install and check

```r
install.packages("mockery")   # if not present
library(mockery)
```

Check `DESCRIPTION` for `Suggests: mockery` to confirm it's available in the project.

### mockery::mock() — replace a function with a stub

```r
library(mockery)

# AI-Generated
test_that("load_config reads file and returns parsed list", {
  # Arrange
  fake_lines <- c("key=value", "count=3")
  stub(load_config, "readLines", fake_lines)

  # Act
  result <- load_config("any/path.ini")

  # Assert
  expect_equal(result$key, "value")
  expect_equal(result$count, "3")
})
```

### mockery::stub() — patch a function within another function's scope

```r
# AI-Generated
test_that("fetch_data calls httr::GET with correct URL", {
  # Arrange
  mock_response <- list(status_code = 200, content = '{"id":1}')
  stub(fetch_data, "httr::GET", mock_response)

  # Act
  result <- fetch_data(user_id = 1)

  # Assert
  expect_equal(result$id, 1)
})
```

### with_mock() (testthat, older API)

```r
# AI-Generated
test_that("get_user returns user name", {
  with_mock(
    `mypackage::call_api` = function(...) list(name = "Alice", id = 1),
    {
      # Act
      result <- get_user(1)

      # Assert
      expect_equal(result$name, "Alice")
    }
  )
})
```

## Expected failures (source bugs)

```r
# AI-Generated — skipped: Bug in float rounding, see GitHub issue #7
test_that("handles float edge case", {
  skip("Bug: rounding error in divide() — see issue #7")
  expect_equal(divide(1.0, 3.0) * 3, 1.0)
})
```
