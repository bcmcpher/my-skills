# LSP Configuration Reference

Language servers give Claude Code real-time diagnostics, go-to-definition, and
find-references beyond what grep can provide. The binary must be installed separately;
`.lsp.json` only tells Claude Code how to connect.

---

## Recommended install pattern

Keep LSP binaries in a dedicated environment independent of any project venv:

```bash
python -m venv ~/.claude-lsp-tools
~/.claude-lsp-tools/bin/pip install pyright
# Add to shell rc: export PATH="$HOME/.claude-lsp-tools/bin:$PATH"
```

---

## Per-language setup

### Python — Pyright

**Install:**
```bash
pip install pyright          # into ~/.claude-lsp-tools or global
# or: npm install -g pyright
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
npm install -g typescript typescript-language-server
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
| LSP binary | `~/.claude-lsp-tools/` or system PATH | What runs |
| Claude connection | `.lsp.json` in project root | How Claude connects |
| Project environment | `pyrightconfig.json`, `tsconfig.json`, etc. | What the LSP checks |

Changing one does not affect the others.
