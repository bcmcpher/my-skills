# Rust Testing Reference

## Framework: Built-in (`#[test]`)

Rust has first-class testing built into the language and `cargo`. No external framework
needed for unit tests. Integration tests live in `tests/`.

## Test file location

- **Unit tests**: in the same file as the source, inside a `#[cfg(test)]` module
- **Integration tests**: `tests/<module>_test.rs` at the crate root

Unit tests alongside source is idiomatic Rust — prefer this pattern.

## Running tests

```bash
cargo test                             # all tests
cargo test module_name                 # tests matching a name pattern
cargo test -- --nocapture              # show println! output
cargo test -- --test-threads=1         # run serially (useful for debugging)
```

## AI-generated marker

Place `// AI-Generated` directly above each `#[test]` function:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    // AI-Generated
    #[test]
    fn test_add_positive_numbers() {
        assert_eq!(add(2, 3), 5);
    }

    // AI-Generated
    #[test]
    fn test_divide_by_zero_returns_err() {
        assert!(divide(1, 0).is_err());
    }
}
```

## Test structure patterns

### Basic assertions

```rust
assert_eq!(result, expected);          // equality (implements PartialEq)
assert_ne!(result, unexpected);        // inequality
assert!(condition);                    // boolean
assert!(result.is_ok());               // Result is Ok
assert!(result.is_err());              // Result is Err
assert!(option.is_some());             // Option is Some
assert!(option.is_none());             // Option is None
```

### Testing Result and Option returns (idiomatic Rust)

```rust
// AI-Generated
#[test]
fn test_parse_valid_input_returns_ok() {
    let result = parse("42");
    assert!(result.is_ok());
    assert_eq!(result.unwrap(), 42);
}

// AI-Generated
#[test]
fn test_parse_invalid_input_returns_err() {
    let result = parse("not-a-number");
    assert!(result.is_err());
}
```

### Testing panics (when panic is the intended behavior)

```rust
// AI-Generated
#[test]
#[should_panic(expected = "index out of bounds")]
fn test_get_out_of_bounds_panics() {
    let v = vec![1, 2, 3];
    let _ = get_element(&v, 10);
}
```

### Parametrized-style (manual, or with rstest crate)

Rust stdlib doesn't have parametrized tests natively. Use multiple test functions or
the `rstest` crate if it's already a dependency:

```rust
// AI-Generated (manual parametrization)
#[test]
fn test_add_various_inputs() {
    let cases = vec![(1, 2, 3), (0, 0, 0), (-1, 1, 0)];
    for (a, b, expected) in cases {
        assert_eq!(add(a, b), expected, "add({}, {}) should be {}", a, b, expected);
    }
}
```

```rust
// AI-Generated (with rstest, if available)
#[cfg(test)]
mod tests {
    use rstest::rstest;
    use super::*;

    // AI-Generated
    #[rstest]
    #[case(1, 2, 3)]
    #[case(0, 0, 0)]
    #[case(-1, 1, 0)]
    fn test_add(#[case] a: i32, #[case] b: i32, #[case] expected: i32) {
        assert_eq!(add(a, b), expected);
    }
}
```

## Integration test structure

```rust
// tests/math_test.rs
use my_crate::math::add;

// AI-Generated
#[test]
fn integration_add_works_across_module_boundary() {
    assert_eq!(add(10, 20), 30);
}
```

## Expected failures (source bugs)

Use `#[ignore]` with a comment:

```rust
// AI-Generated — ignored: overflow bug in saturating_add edge case, see issue #23
#[test]
#[ignore = "Bug: overflow not handled — see issue #23"]
fn test_add_near_i32_max() {
    assert_eq!(add(i32::MAX, 1), i32::MAX); // should saturate, currently panics
}
```
