# R Environment Reference

## Environment indicator

`renv/` directory and/or `renv.lock` in the project root.

---

## renv installed check

Before any renv operations, confirm the package is available:

```bash
Rscript -e "packageVersion('renv')"
```

If this errors, renv is not installed. Install it:

```bash
Rscript -e "install.packages('renv')"
```

---

## Initialize (no lockfile)

If `renv.lock` does not exist, initialize renv for the project:

```bash
Rscript -e "renv::init()"
```

This creates `renv/`, `renv.lock`, and modifies `.Rprofile` to auto-source
`renv/activate.R` on startup.

---

## Restore (lockfile present)

If `renv.lock` already exists, restore the project library to match it:

```bash
Rscript -e "renv::restore()"
```

This installs exactly the versions recorded in the lockfile — reproducible and safe.

---

## Update packages

To update packages to newer versions and record the new state:

```bash
Rscript -e "renv::update()"
```

After updating, snapshot the new state:

```bash
Rscript -e "renv::snapshot()"
```

---

## Verify

```bash
Rscript --version
Rscript -e "renv::status()"
```

`renv::status()` reports whether the project library is in sync with the lockfile. A
clean status means "OK: The project is in a consistent state."

---

## Activate command (for CLAUDE.md)

renv is activated automatically via `.Rprofile` when R starts in the project directory.
The `.Rprofile` line added by `renv::init()` is:

```r
source("renv/activate.R")
```

Document in CLAUDE.md:

```
- Activate: source("renv/activate.R")  # runs automatically via .Rprofile on R startup
```

---

## Recommended hooks

PostToolUse Edit hooks to run after Claude edits an R file:

```
Rscript -e "lintr::lint('$FILE')"
```

Note: lintr must be installed (`install.packages("lintr")`).

---

## Beyond this skill

- **Linter/formatter config** — the hook above runs with lintr defaults. For
  project-specific rules, consult the lintr documentation (`.lintr` config file,
  `styler` package options, etc.).
- **Test runner** — this skill sets up the runtime environment only. Test framework
  setup and configuration (testthat, tinytest, etc.) is a separate step outside the
  scope of `/venv`.

