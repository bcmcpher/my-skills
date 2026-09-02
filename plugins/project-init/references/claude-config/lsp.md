# LSP Configuration Reference

Language servers give Claude Code real-time diagnostics, go-to-definition, and
find-references beyond what grep can provide. The binary must be installed separately;
`.lsp.json` only tells Claude Code how to connect.

---

## Recommended install pattern

LSP servers are **harness tools**, not project dependencies. Adding one to a project's
`pyproject.toml` or `package.json` makes the lockfile lie and breaks the server the next
time that environment is rebuilt. Keep them in dedicated per-language environments,
one per language, shared by every project:

| Language | Home | Create with | Install with |
|---|---|---|---|
| Python | `~/.claude-lsp-tools` | `uv venv ~/.claude-lsp-tools` | `uv pip install --python ~/.claude-lsp-tools/bin/python <pkg>` |
| Node | `~/.claude-node-tools` | `mkdir -p ~/.claude-node-tools` | `npm --prefix ~/.claude-node-tools install -g <pkg>` |

```bash
uv venv ~/.claude-lsp-tools
uv pip install --python ~/.claude-lsp-tools/bin/python pyright
# Add to shell rc: export PATH="$HOME/.claude-lsp-tools/bin:$PATH"
```

`uv venv` deliberately does not install `pip`, so `~/.claude-lsp-tools/bin/pip` does
**not** exist. Use `uv pip install --python <venv>/bin/python`, which targets the venv
without activating it.

Do not `sudo`, and do not install into `/usr/local` — npm's default global prefix, which
is not user-writable on a correctly configured machine.

**Verify it resolves without a login shell.** Claude Code launches servers the same way
hooks run, so anything that depends on `.bashrc` (`nvm`, a `PATH` export, a `pyenv` shim)
is absent:

```bash
env -i PATH="$HOME/.claude-lsp-tools/bin:/usr/bin:/bin" bash -c 'pyright --version'
```

If that fails, give the full path in `.lsp.json`'s `command` array rather than a bare name.

---

## Per-language setup

### Python — Pyright

**Install:**
```bash
uv pip install --python ~/.claude-lsp-tools/bin/python pyright
```

**`.lsp.json`:**
```json
{
  "lspConfig": "./.lsp.json",
  "servers": [
    {
      "name": "pyright",
      "command": ["pyright-langserver", "--stdio"],
      "languages": ["python"],
      "rootPatterns": ["pyproject.toml", "setup.py", "pyrightconfig.json"]
    }
  ]
}
```

**Project type awareness** — create `pyrightconfig.json` in the project root:
```json
{
  "venvPath": ".",
  "venv": ".venv"
}
```
This tells Pyright which virtual environment to use for import resolution.

---

### JavaScript — typescript-language-server

**Install:**
```bash
npm --prefix ~/.claude-node-tools install -g typescript typescript-language-server
```

**`.lsp.json`:**
```json
{
  "lspConfig": "./.lsp.json",
  "servers": [
    {
      "name": "tsserver",
      "command": ["typescript-language-server", "--stdio"],
      "languages": ["javascript"],
      "rootPatterns": ["package.json"]
    }
  ]
}
```

---

### TypeScript — typescript-language-server

Same binary as JavaScript.

**`.lsp.json`:**
```json
{
  "lspConfig": "./.lsp.json",
  "servers": [
    {
      "name": "tsserver",
      "command": ["typescript-language-server", "--stdio"],
      "languages": ["typescript", "javascript"],
      "rootPatterns": ["tsconfig.json", "package.json"]
    }
  ]
}
```

---

### Rust — rust-analyzer

**Install:**
```bash
rustup component add rust-analyzer
# or: download binary from https://github.com/rust-lang/rust-analyzer/releases
```

**`.lsp.json`:**
```json
{
  "lspConfig": "./.lsp.json",
  "servers": [
    {
      "name": "rust-analyzer",
      "command": ["rust-analyzer"],
      "languages": ["rust"],
      "rootPatterns": ["Cargo.toml"]
    }
  ]
}
```

---

### Go — gopls

**Install:**
```bash
go install golang.org/x/tools/gopls@latest
```

**`.lsp.json`:**
```json
{
  "lspConfig": "./.lsp.json",
  "servers": [
    {
      "name": "gopls",
      "command": ["gopls"],
      "languages": ["go"],
      "rootPatterns": ["go.mod"]
    }
  ]
}
```

---

### R — r-languageserver

**Install** (from R console):
```r
install.packages("languageserver")
```

**`.lsp.json`:**
```json
{
  "lspConfig": "./.lsp.json",
  "servers": [
    {
      "name": "r-languageserver",
      "command": ["Rscript", "-e", "languageserver::run()"],
      "languages": ["r"],
      "rootPatterns": ["DESCRIPTION", "renv.lock", ".Rprofile"]
    }
  ]
}
```

---

## plugin.json update

After creating `.lsp.json`, add the reference to `plugin.json` (or the project-level
Claude config if this is a local `.claude/` configuration):

```json
{
  "lspConfig": "./.lsp.json"
}
```

---

## Three independent layers

| Layer | Where | Controls |
|---|---|---|
| LSP binary | `~/.claude-lsp-tools/`, `~/.claude-node-tools/` | What runs |
| Claude connection | `.lsp.json` in project root | How Claude connects |
| Project environment | `pyrightconfig.json`, `tsconfig.json`, etc. | What the LSP checks |

Changing one does not affect the others.
