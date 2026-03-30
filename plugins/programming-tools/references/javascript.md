# JavaScript Testing Reference

## Framework: Jest

Jest is the standard for most JS projects. Check `package.json` for `"jest"` in scripts
or devDependencies. Alternatives include Mocha+Chai and Vitest (see notes below).

## Test file location

- `<module>.test.js` or `<module>.spec.js` alongside the source, or
- `__tests__/<module>.test.js` at the project root
- Check `jest.config.js` or `"jest"` key in `package.json` for configured `testMatch`

## Running tests

```bash
npx jest                             # all tests
npx jest path/to/module.test.js      # specific file
npx jest --testNamePattern "myFn"    # specific test by name
npx jest --verbose                   # verbose
npx jest --coverage                  # with coverage
```

## AI-generated marker

Place `// AI-Generated` directly above each test block:

```javascript
// AI-Generated
test('adds two positive numbers', () => {
  expect(add(2, 3)).toBe(5);
});

describe('MyClass', () => {
  // AI-Generated
  it('throws TypeError for null input', () => {
    expect(() => new MyClass(null)).toThrow(TypeError);
  });
});
```

## Test structure patterns

### Arrange / Act / Assert

```javascript
// AI-Generated
test('divide returns correct quotient', () => {
  // Arrange
  const numerator = 10;
  const denominator = 2;

  // Act
  const result = divide(numerator, denominator);

  // Assert
  expect(result).toBe(5);
});

// AI-Generated
test('divide throws on zero divisor', () => {
  expect(() => divide(1, 0)).toThrow(Error);
});

// AI-Generated
test('divide handles negative numerator', () => {
  // Arrange
  const numerator = -6;
  const denominator = 2;

  // Act
  const result = divide(numerator, denominator);

  // Assert
  expect(result).toBe(-3);
});
```

### describe blocks for grouping

```javascript
describe('add()', () => {
  // AI-Generated
  it('returns sum of two positive numbers', () => {
    expect(add(2, 3)).toBe(5);
  });

  // AI-Generated
  it('returns 0 when both inputs are 0', () => {
    expect(add(0, 0)).toBe(0);
  });

  // AI-Generated
  it('throws TypeError for non-numeric input', () => {
    expect(() => add('a', 1)).toThrow(TypeError);
  });
});
```

### Testing async functions

```javascript
// AI-Generated
test('fetchUser returns user object', async () => {
  const user = await fetchUser(1);
  expect(user).toHaveProperty('id', 1);
});

// AI-Generated
test('fetchUser rejects for invalid id', async () => {
  await expect(fetchUser(-1)).rejects.toThrow();
});
```

## Dependency isolation (mocking)

Unit tests must not reach real networks, filesystems, databases, or external modules.
Use Jest's built-in mock system.

### jest.mock() — module-level mock

```javascript
// Mock an entire module before imports
jest.mock('./db');
jest.mock('axios');

import { saveRecord } from './mymodule';
import { getConnection } from './db';
import axios from 'axios';

// AI-Generated
test('saveRecord calls db.execute', () => {
  // Arrange
  const mockExecute = jest.fn();
  getConnection.mockReturnValue({ execute: mockExecute });

  // Act
  saveRecord({ id: 1, value: 'hello' });

  // Assert
  expect(mockExecute).toHaveBeenCalledTimes(1);
});
```

### jest.fn() — inline mock functions

```javascript
// AI-Generated
test('processItems calls callback for each item', () => {
  // Arrange
  const mockCallback = jest.fn();
  const items = [1, 2, 3];

  // Act
  processItems(items, mockCallback);

  // Assert
  expect(mockCallback).toHaveBeenCalledTimes(3);
  expect(mockCallback).toHaveBeenCalledWith(1);
});
```

### Mocking HTTP requests (axios)

```javascript
jest.mock('axios');
import axios from 'axios';

// AI-Generated
test('fetchUser calls correct endpoint', async () => {
  // Arrange
  axios.get.mockResolvedValue({ data: { id: 1, name: 'Alice' } });

  // Act
  const result = await fetchUser(1);

  // Assert
  expect(result.name).toBe('Alice');
  expect(axios.get).toHaveBeenCalledWith('https://api.example.com/users/1');
});
```

### Resetting mocks between tests

Add to `jest.config.js` to auto-reset:
```javascript
module.exports = {
  clearMocks: true,     // clears mock.calls and mock.instances
  resetMocks: true,     // also resets return values
  restoreMocks: true,   // restores jest.spyOn mocks
};
```

Or reset manually in `afterEach`:
```javascript
afterEach(() => {
  jest.clearAllMocks();
});
```

## Vitest (alternative to Jest)

If the project uses Vitest (`vitest` in devDependencies), the API is nearly identical:

```bash
npx vitest run                # run all tests once
npx vitest run path/to/file  # specific file
```

Imports differ:
```javascript
import { describe, it, expect, vi } from 'vitest';
```

Mocking with Vitest:
```javascript
import { vi } from 'vitest';
vi.mock('./db');
const mockFn = vi.fn();
```

## Expected failures (source bugs)

Jest doesn't have a built-in xfail. Use `.todo` or `.skip` with a comment:

```javascript
// AI-Generated — skipped: Bug in parseFloat edge case, see issue #12
test.skip('handles float string input', () => {
  expect(parseAmount('1.5')).toBe(1.5);
});
```
