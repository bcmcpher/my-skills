# Go Environment Reference

## Environment indicator

`go.sum` file in the module root (created after first `go mod download` or `go get`).

---

## Go version check

Read the required Go version from `go.mod`:

```bash
head -5 go.mod
```

Compare with the installed version:

```bash
go version
```

If the installed version is older than what `go.mod` requires, report the mismatch and
ask the user to upgrade Go before continuing. Do not attempt the upgrade automatically.

---

## Module download

```bash
# Download all module dependencies to the local cache
go mod download

# Tidy: add missing and remove unused dependencies (updates go.sum)
go mod tidy
```

Use `go mod download` for a clean setup. Use `go mod tidy` if the `go.sum` may be
stale or if the user is reconciling dependencies.

---

## Vendor mode

Check for a `vendor/` directory:

```bash
ls vendor/
```

If present, the project uses vendored dependencies. Run:

```bash
go mod vendor
go build ./...
```

The `vendor/` directory must be kept in sync with `go.mod`/`go.sum` — `go mod vendor`
does this.

---

## Verify

```bash
go build ./...
```

A successful build with no errors confirms the environment is functional.

```bash
go version
```

---

## No activate concept

Go does not use per-project environment activation. Dependencies are cached in
`$GOMODCACHE` (default: `~/go/pkg/mod`) and the project is identified by its module
path in `go.mod`. Document in CLAUDE.md:

```
- Activate: n/a (Go modules are resolved automatically; no activation needed)
```

If `$GOPATH` or `$GOMODCACHE` is set to a non-standard location, note those values in
the CLAUDE.md section for reference.

---

## Recommended hooks

PostToolUse Edit hooks to run after Claude edits a Go file:

```
go vet ./...
```

```
gofmt -w $FILE
```

---

## Beyond this skill

- **Linter/formatter config** — the hooks above run with tool defaults. For
  project-specific rules, consult the tool's documentation (`.golangci.yml` for
  golangci-lint, etc.). `gofmt` itself has no configuration.
- **Test runner** — this skill sets up the runtime environment only. Test framework
  setup and configuration (`go test`, `testify`, etc.) is a separate step outside the
  scope of `/venv`.
