@RTK.md

# Harness tool environments

Global CLI dependencies that Claude Code itself relies on — hook binaries, LSP servers, harness
CLIs — live in dedicated per-language environments. Never a project environment, never a system
package path, never `nvm`.

| Language | Home | Create with | Install with |
|---|---|---|---|
| Python | `~/.claude-lsp-tools` | `uv venv ~/.claude-lsp-tools` | `uv pip install --python ~/.claude-lsp-tools/bin/python <pkg>` |
| Node | `~/.claude-node-tools` | `mkdir -p ~/.claude-node-tools` | `npm --prefix ~/.claude-node-tools install -g <pkg>` |

`uv venv` deliberately does not install `pip`, so `~/.claude-lsp-tools/bin/pip` does not exist —
use `uv pip install --python <venv>/bin/python`, which targets the venv without activating it.

Currently: `code-review-graph`, `pyright`, `yt-dlp`, `zotero-cli`/`zotero-mcp` and `opencite` in
the first, `@fission-ai/openspec` in the second.

The `opencite` skill's examples all say `uvx opencite`. Use the installed `opencite` instead: it
is pinned in `config/tools/python-lock.txt`, and `uvx opencite` cannot reach the `[pdf]` extra
those examples assume (that would need `uvx --from 'opencite[pdf]' opencite`), so PDF retrieval
and conversion fail under `uvx`.

Harness tools are not project dependencies. Adding one to a project's `pyproject.toml` or
`package.json` makes the lockfile lie and breaks the tool when that environment is rebuilt.

`nvm` is specifically unsuitable: it is a shell function sourced from `.bashrc`, so
`~/.nvm/versions/node/*/bin` is absent in non-interactive shells — exactly where hooks run. For
the same reason, hook commands in `settings.json` use an explicit `~/.claude-*-tools/bin/<cmd>`
path rather than a bare name.

Before wiring a new tool into a hook, confirm it resolves without a login shell:

```bash
env -i PATH="$HOME/.claude-lsp-tools/bin:/usr/bin:/bin" bash -c '<cmd> --version'
```

Do not `sudo`, and do not install into `/usr/local` — npm's default prefix, which is not
user-writable here by design.
