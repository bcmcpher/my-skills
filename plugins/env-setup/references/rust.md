# Rust Environment Reference

## Environment indicator

`target/` directory and/or `Cargo.lock` file in the crate root.

---

## rustup check

```bash
rustup show
```

This prints the active toolchain and installed targets. If rustup is not installed,
surface the exact install command and ask the user to run it manually:

```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

---

## rust-toolchain.toml

If `rust-toolchain.toml` or `rust-toolchain` exists, rustup reads it automatically and
installs the pinned channel/version when any `cargo` or `rustup` command runs. No
special handling needed — note this to the user as confirmation that the toolchain is
pinned.

---

## Fetch and build

```bash
# Download dependencies without building (fast, confirms registry access)
cargo fetch

# Full build (also fetches if needed)
cargo build
```

For `--recreate`: delete the `target/` directory, then run `cargo build`.

```bash
rm -rf target/
cargo build
```

---

## Workspace note

Check `Cargo.toml` for a `[workspace]` table:

```bash
grep -l '^\[workspace\]' Cargo.toml
```

If present, always run `cargo` commands from the workspace root — they apply to all
member crates automatically.

---

## Verify

```bash
cargo --version
rustc --version
```

Both must resolve to the toolchain shown by `rustup show`.

---

## No activate concept

Rust does not use per-project environment activation. The toolchain is global (managed by
rustup) and the build artifacts live in `target/`. Document this in CLAUDE.md:

```
- Activate: n/a (rustup manages toolchain globally; run cargo commands from project root)
```

---

## Recommended hooks

PostToolUse Edit hooks to run after Claude edits a Rust file:

```
cargo clippy -- -D warnings
```

---

## Beyond this skill

- **Linter/formatter config** — the hooks above run with tool defaults. For
  project-specific rules, consult the tool's documentation (`clippy.toml`,
  `.clippy.toml`, `rustfmt.toml`, etc.).
- **Test runner** — this skill sets up the runtime environment only. Test framework
  setup and configuration (`cargo test`, `nextest`, etc.) is a separate step outside
  the scope of `/venv`.
