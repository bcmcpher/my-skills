# config/ — Global Claude Code configuration

Versioned copy of the portable files from `~/.claude/`, plus the handful of tool configs that
live elsewhere but are still part of the global Claude Code layer. Use `bin/sync-config` to keep
this directory and your live config in sync.

## What's tracked

| File | Source | Purpose |
|---|---|---|
| `settings.json` | `~/.claude/settings.json` | Permissions, hook wiring, enabled plugins, known marketplaces |
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Global instructions — imports `RTK.md`, documents the tool environments |
| `RTK.md` | `~/.claude/RTK.md` | rtk command reference, imported by `CLAUDE.md` |
| `statusline-command.sh` | `~/.claude/statusline-command.sh` | Status line; referenced by the `statusLine` block in `settings.json` |
| `hooks/protect-files.sh` | `~/.claude/hooks/protect-files.sh` | PreToolUse guard — blocks edits to protected files |
| `hooks/bash-guard.sh` | `~/.claude/hooks/bash-guard.sh` | PreToolUse guard — blocks what the permission globs cannot express |
| `hooks/notify.sh` | `~/.claude/hooks/notify.sh` | Notification hook — desktop alert when a prompt is waiting |
| `xdg/openspec/config.json` | `~/.config/openspec/config.json` | openspec profile + telemetry opt-out |
| `xdg/caveman/config.json` | `~/.config/caveman/config.json` | caveman default mode |
| `skills/<name>/SKILL.md` | `~/.claude/skills/<name>/SKILL.md` | Standalone global skills (none tracked at present) |

### One value is deliberately stripped

`pull` deletes `extraKnownMarketplaces.local` from the tracked `settings.json`. That entry records
an absolute path to wherever this repo was cloned, so leaving it in means a `push` on another
machine registers a marketplace pointing at a directory that does not exist. After cloning on a
new machine, re-add it:

```bash
claude plugin marketplace add "$(pwd)"   # from this repo's root
```

Nothing else in the tracked config contains an absolute path — `grep -nE '"/[^"]*"'
config/settings.json` should return nothing. Hook commands use `~/`-relative paths, which are
portable.

The two `xdg/` files matter more than their size suggests: without them a new machine silently
gets tool defaults. openspec re-enables telemetry, and caveman starts in mode `full` rather than
`lite`.

## What's NOT tracked

- `~/.claude/.credentials.json` — auth tokens, never commit
- `~/.claude/history.jsonl`, `cache/`, `session-env/`, `projects/`, `sessions/` — runtime state
- `~/.claude/plugins/` — the marketplace cache. Plugin *sources* live in `plugins/` in this repo;
  the cache is rebuilt by `claude plugin marketplace add`. `sync-config` explicitly excludes it
  from the `.mcp.json` scan, which otherwise drags in every third-party marketplace's MCP config.
- Per-repo config — `openspec/` directories, per-project `.mcp.json`, `code-review-graph` graphs.
  These regenerate per repo and are not global.

## Sync workflow

```bash
# Pull live config into this repo (after changing settings in Claude)
bin/sync-config pull

# Push repo config to ~/.claude/ (on a new machine or after editing here)
bin/sync-config push
```

⚠️ **`push` overwrites, and `pull` never deletes.** On a machine where the live config is newer
than this directory, `push` silently reverts it — always `pull` first if you are unsure which
side is authoritative. And because `pull` only ever copies, a file you delete from `~/.claude/`
survives here until you remove it by hand.

## External dependencies

`settings.json` references binaries that are not installed by this repo. They live in dedicated
per-language environments, deliberately kept off any project environment:

| Tool | Home | Used by |
|---|---|---|
| `rtk` | `~/.local/bin` | PreToolUse Bash hook |
| `code-review-graph` | `~/.claude-lsp-tools` (venv) | PostToolUse / SessionStart / SessionEnd, via `graph-update.sh` |
| `pyright` | `~/.claude-lsp-tools` (venv) | `pyright-lsp` plugin, per-project |
| `openspec` | `~/.claude-node-tools` (npm prefix) | `openspec init` per repo |
| `jq` | system | both hooks and the status line |

Recreate them on a new machine with `bin/rebuild-tools`, which reads the manifests in
`config/tools/`:

```bash
bin/rebuild-tools            # rebuild both envs from the lock files
bin/rebuild-tools --latest   # re-resolve from the intent files, ignoring the locks
bin/rebuild-tools --check    # verify only; changes nothing, exits 1 on a problem
```

| Manifest | Holds |
|---|---|
| `config/tools/python-tools.txt` | intent — the packages actually wanted |
| `config/tools/python-lock.txt` | the resolved closure, for a reproducible rebuild |
| `config/tools/node-tools.txt` | intent |
| `config/tools/node-lock.txt` | pinned versions |

`uv venv` does not install `pip`, so there is no `~/.claude-lsp-tools/bin/pip` — use
`uv pip install --python <venv>/bin/python`, which targets the venv without activating it.
`rebuild-tools` does this for you, and finishes by checking each binary resolves under
`env -i` — a tool that works in your shell but not in a hook is the failure this layout exists
to prevent.

Add both `bin/` directories to `PATH` in your shell rc. Hook commands in `settings.json` use the
explicit `~/.claude-*-tools/bin/<cmd>` path rather than a bare name, because hooks run in
non-interactive shells where a `.bashrc` PATH edit has not been applied. For the same reason
these tools must not be installed under `nvm`, whose shell function is absent non-interactively.

## Per-repo opt-in for code-review-graph

The three `code-review-graph` hooks are wired globally so the wiring lives in one place and
travels with this config — but they run through `hooks/graph-update.sh`, which returns early
unless the current repository already contains a `.code-review-graph/` directory.

```bash
cd <repo> && code-review-graph build      # opt in
rm -rf <repo>/.code-review-graph          # opt out
```

Without the gate, global wiring fails **open**: every repository ever edited gets a graph built
in it, including clones of other people's projects and repos that track no code at all. The gate
also makes non-repository directories a clean skip, rather than a hook that exits non-zero on
every session and has to be silenced with `|| true`.

Opting in adds nothing to the repo's index — `.code-review-graph/` ships its own `.gitignore`
covering itself. Which repos are opted in is therefore machine-local state, not something this
repo restores; a graph is derived data that rebuilds in seconds, and choosing per repo on a new
machine is the point.

Upstream's alternative is `code-review-graph install` run per repo. It writes
`.claude/settings.json`, `.mcp.json`, graph instructions appended to `CLAUDE.md`, and a git
pre-commit hook into the worktree — all committed, and all referencing `~/.claude-lsp-tools`
paths that exist only on this machine.

## Adding a new global hook

1. Write the script and place it in `config/hooks/`
2. Wire it in `config/settings.json` under `hooks.PreToolUse` or `hooks.PostToolUse`
3. Test it against both cases before wiring — a command it must block, and a similar one it must
   let through. The deleted `git-guard.sh` matched `.git/` anywhere in the command text and so
   blocked the ordinary idiom `find . -not -path "./.git/*"`.
4. Run `bin/sync-config push` to apply

## Adding a new standalone skill

Standalone skills (no plugin wrapper) live in `~/.claude/skills/<name>/SKILL.md`.
To track one here:

1. Copy `~/.claude/skills/<name>/` into `config/skills/<name>/`
2. Run `bin/sync-config pull` going forward to keep it in sync

To promote a standalone skill to a full plugin, copy it to `plugins/<name>/` using
`bin/new-plugin skill <name>` and move the SKILL.md content there.

## Tracking another external config

Add its path, relative to `$XDG_CONFIG_HOME` (default `~/.config`), to the `XDG_TRACKED` array
near the top of `bin/sync-config`. Both directions pick it up automatically.
