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

### Typed inputs and assertions

```typescript
import { add } from './math';

// AI-Generated
test('add returns correct sum', () => {
  const result: number = add(2, 3);
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
    const user: User = service.getUser(1);
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
  const data: ApiResponse = await fetchData('/endpoint');
  expect(data.status).toBe('ok');
});
```

## Expected failures

```typescript
// AI-Generated — skipped: Generic type constraint bug, see issue #34
test.skip('handles union type input', () => {
  expect(process<string | number>('hello')).toBe('HELLO');
});
```

## Note on type errors vs. runtime errors

TypeScript catches many errors at compile time. When writing tests for type-level
constraints, note them in a comment but focus tests on runtime behavior — that's what
tests actually verify.
