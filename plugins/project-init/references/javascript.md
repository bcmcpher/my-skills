# JavaScript Environment Reference

## Environment indicator

`node_modules/` directory in the project root.

---

## Node version

Check for `.nvmrc` in the project root:

```bash
ls .nvmrc
```

If present, run:

```bash
nvm use
```

This switches to the pinned Node version before installing packages. If nvm is not
installed or `.nvmrc` is absent, use the currently active Node version.

---

## Package manager detection

Check lockfiles in this order:

| Lockfile present | Package manager |
|---|---|
| `pnpm-lock.yaml` | pnpm |
| `yarn.lock` | yarn |
| `package-lock.json` | npm |
| None | npm (default) |

---

## Install commands

```bash
# npm
npm install

# yarn
yarn install

# pnpm
pnpm install
```

For `--recreate`: delete `node_modules/` first, then run the install command above.

---

## Verify

```bash
node --version
which node
```

If nvm is in use, `which node` should resolve to a path under `~/.nvm/versions/node/`.

---

## Activate command (for CLAUDE.md)

```
nvm use
```

If no `.nvmrc` is present, record the Node version in use instead:

```
node v<version> (system or nvm default)
```

---

## Recommended hooks

PostToolUse Edit hooks to run after Claude edits a JavaScript file:

```
npx eslint --fix $FILE
```

---

## Beyond this skill

- **Linter/formatter config** — the hooks above run with tool defaults. For
  project-specific rules, consult the tool's documentation (`.eslintrc.json`,
  `.eslintrc.cjs`, `prettier.config.js`, etc.).
- **Test runner** — this skill sets up the runtime environment only. Test framework
  setup and configuration (Jest, Vitest, Mocha, etc.) is a separate step outside the
  scope of `/venv`.
