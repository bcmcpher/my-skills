# codebase-audit

`/codebase-audit [repo-path]` runs a whole-repository quality audit of a Python package,
its tests and its OpenSpec specs. Scripts sweep every site; the model judges each
candidate; findings are triaged into work units.

## Why scripts

An audit fails when a dimension is sampled and reported as swept. The scripts make every
dimension exhaustive and countable. The model reads candidates and decides; it does not
search.

## Scripts

All live in `skills/codebase-audit/scripts/`. They use the standard library only, parse
code with `ast`, and never import the code under audit. Run them with the project's own
interpreter, so `ast` accepts its syntax. Each prints markdown, or JSON with `--json`.

| Script | Dimension |
|---|---|
| `inventory.py` | module sizes; outlines of large modules for split points |
| `dup_logic.py` | identical and same-shape bodies, repeated blocks, optional-import guards |
| `public_callers.py` | public definitions called only by tests, or by nothing |
| `raise_taxonomy.py` | every `raise` by kind of check and exception type |
| `docstring_signature.py` | numpydoc `Parameters` against names, defaults and `Literal` values |
| `test_near_dupes.py` | argument-only, accessor-only and class-pair test clusters |
| `coverage_subsets.py` | coverage-subset test pairs under one requirement marker |
| `test_private_access.py` | tests that import private names or read private attributes |
| `spec_inventory.py` | small capabilities, name families, near-duplicate and mechanics-worded requirements, marker map |

## Tests

Each script has a test against a planted case in `tests/fixture/`:

```bash
uv run --no-project --python 3.12 --with pytest --with pytest-cov pytest plugins/codebase-audit/tests
```

## Origin

Built after three external audit passes of crane left most sweeps sampled. First run:
crane, 2026-10-23.
