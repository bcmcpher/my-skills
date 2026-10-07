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
the first, `@fission-ai/openspec` and `deno` in the second, and `bids-validator` (the schema
validator, JSR-only) run by that `deno` through a wrapper in the second's `bin/`. `igraph` is
there too — a library rather than a CLI, supplying `code-review-graph`'s `communities` extra,
without which community detection falls back to grouping by directory and only restates the file
tree.

`config/tools/python-tools.txt`, `node-tools.txt` and `deno-tools.txt` are the authority on that
list; `bin/rebuild-tools --check` verifies the live environments against the locks.

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

# New features run on a branch

Build every new feature on its own branch, never directly on `main`, whatever drives it: an
OpenSpec change, a science-superpowers plan, or an ordinary plan. The branch exists so the
feature has a reviewable diff: before it merges, run `/code-review` against it and resolve the
findings. Ask before merging to `main` and before pushing.

- OpenSpec changes: `change/<change-id>`.
- Science-superpowers and other plans: `plan/<plan-slug>`. Plan ticks and "As built" notes are
  committed on the same branch as the code.

Create the branch before the feature's first commit.

## OpenSpec specifics

In a superproject with submodules, branch every repo the change touches under the same name.
Code commits go to the submodule branch; spec deltas, docs and `tasks.md` ticks go to the
parent branch, whose commits pin the submodule at its branch HEAD. Merge the submodule first,
then the parent, so the parent never pins a commit that is not on the submodule's `main`.

Archive the OpenSpec change on its branch, before the merge, so the archive, the promoted
specs and the code reach `main` together in one merge. Then `openspec/specs/` never disagrees
with the code on `main`. In a superproject, archive on the parent branch.
