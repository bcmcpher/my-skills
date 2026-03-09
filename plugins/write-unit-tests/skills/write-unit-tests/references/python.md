# Python Testing Reference

## Framework: pytest

Use pytest unless the project already has `unittest` tests — check for `import unittest`
or a `setUp`/`tearDown` pattern before deciding.

## Test file location

- Preferred: `tests/test_<module>.py` at the project root
- Alternative: `test_<module>.py` alongside the source file
- Check `pyproject.toml` or `pytest.ini` for a configured `testpaths`

## Running tests

```bash
pytest                                      # all tests
pytest tests/test_mymodule.py               # specific file
pytest tests/test_mymodule.py::test_fn -v  # specific test
pytest -v                                   # verbose
pytest --cov=src tests/                     # with coverage
```

## AI-generated marker

Use the `@pytest.mark.ai_generated` decorator on every AI-written test:

```python
import pytest

@pytest.mark.ai_generated
def test_add_happy_path():
    assert add(2, 3) == 5

@pytest.mark.ai_generated
class TestMyClass:
    def test_method_returns_expected(self):
        ...
```

Register the mark in `pytest.ini` or `pyproject.toml` to suppress the unknown-mark warning:

```ini
# pytest.ini
[pytest]
markers =
    ai_generated: marks tests as AI-generated (for audit purposes)
```

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = ["ai_generated: marks tests as AI-generated (for audit purposes)"]
```

## Test structure patterns

### Simple function tests

```python
@pytest.mark.ai_generated
def test_divide_happy_path():
    assert divide(10, 2) == 5.0

@pytest.mark.ai_generated
def test_divide_by_zero_raises():
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

@pytest.mark.ai_generated
def test_divide_negative_numerator():
    assert divide(-6, 2) == -3.0
```

### Parametrize for multiple input cases

```python
@pytest.mark.ai_generated
@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (100, -50, 50),
])
def test_add_parametrized(a, b, expected):
    assert add(a, b) == expected
```

### Fixtures for shared setup

```python
@pytest.fixture
def sample_user():
    return User(name="Alice", email="alice@example.com")

@pytest.mark.ai_generated
def test_user_display_name(sample_user):
    assert sample_user.display_name() == "Alice"
```

### Expected failures (source bugs found during testing)

If a test reveals a bug in the source code, do not fix the source — mark the test as xfail:

```python
@pytest.mark.ai_generated
@pytest.mark.xfail(reason="Bug: divide() doesn't handle float inputs — see issue #42")
def test_divide_float_inputs():
    assert divide(1.5, 0.5) == 3.0
```

## Appending to existing test files

If the test file already has test classes or functions, add new tests at the end.
If a `TestClassName` class exists for the unit you're testing, add methods inside it.
Never reorder, modify, or delete existing tests.
