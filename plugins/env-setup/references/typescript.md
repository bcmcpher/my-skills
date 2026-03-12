# TypeScript Environment Reference

## Environment indicator

`node_modules/` directory in the project root.

---

## Install workflow

TypeScript projects use the same Node and package manager detection as JavaScript.
Follow the steps in `javascript.md` for:

- Node version (`.nvmrc` / `nvm use`)
- Package manager detection (`pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`)
- Install commands (`npm install`, `yarn install`, `pnpm install`)

After running the install, continue with the TypeScript-specific steps below.

---

## tsconfig.json check

After install, verify `tsconfig.json` exists:

```bash
ls tsconfig.json
```

If absent, the project may not be configured for TypeScript compilation — note this to
the user but do not create one automatically (project config is out of scope).

If present, note any `paths` aliases: these affect how imports resolve and may require
additional LSP configuration.

---

## Build verify

Run a type check (no output files) to confirm no compile errors in the freshly installed
environment:

```bash
npx tsc --noEmit
```

Report any errors to the user. Do not attempt to fix type errors — that is source code
modification outside this skill's scope.

---

## pyrightconfig.json note

If `pyrightconfig.json` is absent, offer to create a minimal one to help Pyright/LSP
locate the `node_modules` types:

```json
{
  "include": ["src"],
  "exclude": ["node_modules"]
}
```

---

## Verify

```bash
node --version
which node
npx tsc --version
```

---

## Activate command (for CLAUDE.md)

```
nvm use
```

If no `.nvmrc` is present, record the Node version in use instead.

---

## Recommended hooks

PostToolUse Edit hooks to run after Claude edits a TypeScript file:

```
npx eslint --fix $FILE
```

```
npx tsc --noEmit
```

---

## Beyond this skill

- **Linter/formatter config** — the hooks above run with tool defaults. For
  project-specific rules, consult the tool's documentation (`.eslintrc.json`,
  `.eslintrc.cjs`, `prettier.config.ts`, etc.).
- **Test runner** — this skill sets up the runtime environment only. Test framework
  setup and configuration (Jest, Vitest, etc.) is a separate step outside the scope
  of `/venv`.
