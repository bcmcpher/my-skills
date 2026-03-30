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

### Arrange / Act / Assert

```python
@pytest.mark.ai_generated
def test_divide_happy_path():
    # Arrange
    numerator, denominator = 10, 2

    # Act
    result = divide(numerator, denominator)

    # Assert
    assert result == 5.0

@pytest.mark.ai_generated
def test_divide_by_zero_raises():
    # Arrange / Act / Assert (combined for simple exception checks)
    with pytest.raises(ZeroDivisionError):
        divide(1, 0)

@pytest.mark.ai_generated
def test_divide_negative_numerator():
    # Arrange
    numerator, denominator = -6, 2

    # Act
    result = divide(numerator, denominator)

    # Assert
    assert result == -3.0
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

## Dependency isolation (mocking)

Unit tests must not reach real filesystems, networks, databases, or external modules.
Use `unittest.mock` (stdlib) or `pytest-mock` (preferred with pytest).

### pytest-mock (recommended)

`pytest-mock` provides a `mocker` fixture that auto-cleans up after each test:

```python
# Arrange
@pytest.mark.ai_generated
def test_load_config_reads_file(mocker):
    mock_open = mocker.mock_open(read_data="key=value\n")
    mocker.patch("builtins.open", mock_open)

    # Act
    result = load_config("any/path.ini")

    # Assert
    assert result == {"key": "value"}
    mock_open.assert_called_once_with("any/path.ini", "r")
```

### unittest.mock (stdlib)

```python
from unittest.mock import patch, MagicMock

@pytest.mark.ai_generated
def test_fetch_user_calls_api(mocker):
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": 1, "name": "Alice"}

    with patch("mymodule.requests.get", return_value=mock_response) as mock_get:
        # Act
        result = fetch_user(1)

    # Assert
    assert result["name"] == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### Mocking classes and methods

```python
@pytest.mark.ai_generated
def test_save_record_calls_db(mocker):
    # Arrange
    mock_db = mocker.MagicMock()
    mocker.patch("mymodule.get_db_connection", return_value=mock_db)

    # Act
    save_record({"id": 1, "value": "hello"})

    # Assert
    mock_db.execute.assert_called_once()
```

### Check if pytest-mock is available

```bash
pip show pytest-mock   # installed?
```

If not available, use `unittest.mock` with `@patch` decorator or context manager instead.

## Appending to existing test files

If the test file already has test classes or functions, add new tests at the end.
If a `TestClassName` class exists for the unit you're testing, add methods inside it.
Never reorder, modify, or delete existing tests.
