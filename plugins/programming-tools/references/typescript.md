# TypeScript Testing Reference

## Framework: Jest + ts-jest (or Vitest)

Check `package.json` for `ts-jest` or `@jest/globals` in devDependencies. Vitest has
native TypeScript support and is common in Vite-based projects.

## Test file location

- `<module>.test.ts` or `<module>.spec.ts` alongside source, or
- `__tests__/<module>.test.ts`
- Check `jest.config.ts` or `vitest.config.ts` for configured paths

## Running tests

```bash
# Jest + ts-jest
npx jest
npx jest path/to/module.test.ts --verbose

# Vitest
npx vitest run
npx vitest run path/to/module.test.ts
```

## AI-generated marker

Place `// AI-Generated` directly above each test:

```typescript
// AI-Generated
test('parses valid user object', () => {
  const result = parseUser({ id: 1, name: 'Alice' });
  expect(result.name).toBe('Alice');
});
```

## Test structure patterns

### Arrange / Act / Assert with typed inputs

```typescript
import { add } from './math';

// AI-Generated
test('add returns correct sum', () => {
  // Arrange
  const a: number = 2;
  const b: number = 3;

  // Act
  const result: number = add(a, b);

  // Assert
  expect(result).toBe(5);
});

// AI-Generated
test('add throws for non-numeric input', () => {
  // TypeScript may catch this at compile time, but test runtime behavior too
  expect(() => add('a' as unknown as number, 1)).toThrow(TypeError);
});
```

### Testing classes with interfaces

```typescript
import { UserService } from './user-service';
import type { User } from './types';

describe('UserService', () => {
  let service: UserService;

  beforeEach(() => {
    service = new UserService();
  });

  // AI-Generated
  it('returns typed User object', () => {
    // Arrange / Act
    const user: User = service.getUser(1);

    // Assert
    expect(user).toMatchObject({ id: 1 });
  });

  // AI-Generated
  it('throws for missing user', () => {
    expect(() => service.getUser(-1)).toThrow();
  });
});
```

### Async with proper types

```typescript
// AI-Generated
test('fetchData resolves with typed response', async () => {
  // Arrange / Act
  const data: ApiResponse = await fetchData('/endpoint');

  // Assert
  expect(data.status).toBe('ok');
});
```

## Dependency isolation (mocking)

Unit tests must not reach real networks, filesystems, databases, or external modules.
Use Jest's mock system with TypeScript-aware patterns.

### jest.mock() with typed mocks

```typescript
jest.mock('./db');
jest.mock('axios');

import { saveRecord } from './mymodule';
import { getConnection } from './db';
import axios from 'axios';

// Cast to jest.MockedFunction for type-safe mock access
const mockGetConnection = getConnection as jest.MockedFunction<typeof getConnection>;
const mockAxiosGet = axios.get as jest.MockedFunction<typeof axios.get>;

// AI-Generated
test('saveRecord calls db.execute', () => {
  // Arrange
  const mockExecute = jest.fn();
  mockGetConnection.mockReturnValue({ execute: mockExecute } as any);

  // Act
  saveRecord({ id: 1, value: 'hello' });

  // Assert
  expect(mockExecute).toHaveBeenCalledTimes(1);
});
```

### jest.spyOn for partial mocks

```typescript
import * as userModule from './user';

// AI-Generated
test('processUser calls formatName', () => {
  // Arrange
  const spy = jest.spyOn(userModule, 'formatName').mockReturnValue('ALICE');

  // Act
  const result = processUser({ name: 'alice' });

  // Assert
  expect(result.displayName).toBe('ALICE');
  spy.mockRestore();
});
```

### Mocking HTTP (axios)

```typescript
jest.mock('axios');
import axios from 'axios';
const mockAxios = axios as jest.Mocked<typeof axios>;

// AI-Generated
test('fetchUser calls correct endpoint', async () => {
  // Arrange
  mockAxios.get.mockResolvedValue({ data: { id: 1, name: 'Alice' } });

  // Act
  const result = await fetchUser(1);

  // Assert
  expect(result.name).toBe('Alice');
  expect(mockAxios.get).toHaveBeenCalledWith('https://api.example.com/users/1');
});
```

### Vitest mocking (if using Vitest)

```typescript
import { vi } from 'vitest';
import type { MockedFunction } from 'vitest';

vi.mock('./db');
import { getConnection } from './db';
const mockGetConnection = getConnection as MockedFunction<typeof getConnection>;
```

## Note on type errors vs. runtime errors

TypeScript catches many errors at compile time. When writing tests for type-level
constraints, note them in a comment but focus tests on runtime behavior — that's what
tests actually verify.

## Expected failures

```typescript
// AI-Generated — skipped: Generic type constraint bug, see issue #34
test.skip('handles union type input', () => {
  expect(process<string | number>('hello')).toBe('HELLO');
});
```
