# config/ — Global Claude Code configuration

Versioned copy of the portable files from `~/.claude/`, plus the handful of tool configs that
live elsewhere but are still part of the global Claude Code layer. Use `bin/sync-config` to keep
this directory and your live config in sync.

After changing anything here, work through [`VERIFY.md`](VERIFY.md) in a fresh session.

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
| `skills/youtube-transcript/SKILL.md` | `~/.claude/skills/youtube-transcript/SKILL.md` | Hand-written global skill — pulls YouTube captions via `yt-dlp` |

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
- `~/.opencite/config.toml` — opencite's API keys, same reason
- `~/.claude/history.jsonl`, `cache/`, `session-env/`, `projects/`, `sessions/` — runtime state
- `~/.claude/plugins/` — the marketplace cache. Plugin *sources* live in `plugins/` in this repo;
  the cache is rebuilt by `claude plugin marketplace add`. `sync-config` explicitly excludes it
  from the `.mcp.json` scan, which otherwise drags in every third-party marketplace's MCP config.
- Per-repo config — `openspec/` directories, per-project `.mcp.json`, `code-review-graph` graphs.
  These regenerate per repo and are not global.
- **Generated global skills** — `~/.claude/skills/zotero-cli/`, and the flat `~/.claude/skills/*.md`
  that `code-review-graph install --global` writes. These are emitted by their own tool and are
  reproduced by re-running its installer, not by copying a snapshot. Tracking one means the repo
  copy silently drifts from whatever version the package actually installs. `sync-config` copies
  only `SKILL.md` from a skill directory anyway, so `zotero-cli/reference.md` would be lost.
  Contrast `skills/youtube-transcript/`, which is hand-written, has no generator, and *is* tracked.

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

**`push` is for bootstrapping a new machine, not for applying a single change to a working one.**
It copies `settings.json` wholesale, so on an established machine it reverts every live-only key
the baseline deliberately does not carry — per-machine `enabledPlugins` (`pyright-lsp`,
`project-init`), the `extraKnownMarketplaces.local` absolute path, absolute-path deny rules. To
land one change on a machine already in use, edit `config/` (still the source of truth), then
hand-apply the same edit live — `jq` for `settings.json`, `cp` for a hook or skill. Do not reach
for `pull` to reconcile afterwards; that contaminates the baseline with exactly the state listed
above.

## External dependencies

`settings.json` references binaries that are not installed by this repo. They live in dedicated
per-language environments, deliberately kept off any project environment:

| Tool | Home | Used by |
|---|---|---|
| `rtk` | `~/.local/bin` | PreToolUse Bash hook |
| `code-review-graph` | `~/.claude-lsp-tools` (venv) | PostToolUse / SessionStart / SessionEnd, via `graph-update.sh` |
| `pyright` | `~/.claude-lsp-tools` (venv) | `pyright-lsp` plugin, per-project |
| `yt-dlp` | `~/.claude-lsp-tools` (venv) | the `youtube-transcript` skill |
| `zotero-cli`, `zotero-mcp` | `~/.claude-lsp-tools` (venv) | the `zotero-cli` skill |
| `opencite` | `~/.claude-lsp-tools` (venv) | the `opencite` skill (`opencite@research-skills`) |
| `openspec` | `~/.claude-node-tools` (npm prefix) | `openspec init` per repo |
| `jq` | system | both hooks and the status line |

Recreate them on a new machine with `bin/rebuild-tools`, which reads the manifests in
`config/tools/`:

```bash
bin/rebuild-tools            # rebuild both envs from the lock files
bin/rebuild-tools --latest   # re-resolve from the intent files, ignoring the locks
bin/rebuild-tools --check    # verify only; changes nothing, exits 1 on a problem
bin/rebuild-tools --freeze   # record the current envs into the lock files
```

| Manifest | Holds | Edited by |
|---|---|---|
| `config/tools/python-tools.txt` | intent — the packages actually wanted | you |
| `config/tools/python-lock.txt` | the resolved closure, for a reproducible rebuild | `--freeze` |
| `config/tools/node-tools.txt` | intent | you |
| `config/tools/node-lock.txt` | pinned versions | `--freeze` |

`--check` compares the live environments against the locks, so it is the only drift detector in
this setup — an unplanned version bump shows up there. That is why `--freeze` is a deliberate
command and **not** part of `bin/sync-config pull`: a lock regenerated on every sync would agree
with the environment by construction, `--check` could never fail, and a version you did not
choose would be committed as though you had. `--freeze` refuses to write a lock from an
environment that is missing something the intent files ask for.

The usual sequence for upgrading a tool is `--latest`, then `--check`, then `--freeze` once the
resulting diff looks right.

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

## `rm` is gated, not denied

`rm -rf *` and `rm -f *` used to sit in `deny`. They were removed. Two reasons:

1. **Deny is absolute.** Every legitimate `rm -rf ./build` was a dead end with no way to approve
   it, which is a steady source of friction against no observed unsafe case.
2. **The globs gave less protection than they looked like.** Permission patterns anchor to the
   start of the command string, so `cd x && rm -rf /`, `rm -fr /`, `rm -Rf /`,
   `rm --recursive --force /` and `xargs rm -rf` all walked straight past them.

Ordinary `rm` now sits in `ask` (`Bash(rm *)`, `Bash(rtk rm *)`) — it prompts, and you can approve
it. Beneath that prompt, **rule 5 of `bash-guard.sh`** is a hard floor for targets that should stay
impossible regardless of what the prompt says: the filesystem root, `$HOME`, `/etc /usr /var /bin
/sbin /boot /lib /lib64 /opt /root`, the mount roots `/home /srv /mnt /media`, `..`, and
`~/.ssh ~/.aws ~/.gnupg`. Like every other rule in that file it matches an argument position, so it
catches all flag spellings and any position in a pipeline.

`/home` is on that list because `$HOME` is — a floor whose parent is not a floor is not a floor.
The other three mount roots follow the same reasoning and cost nothing, since whole-target matching
lets `rm -rf /mnt/scratch/build` through.

Two narrowings are deliberate and should not be "fixed" later:

- **Whole-target match, never a prefix.** `rm -rf /tmp/scratch`, `rm -rf /tmp/*` and
  `rm -rf ~/Projects/x/node_modules` are ordinary work and must pass. Only the bare root is a floor.
- **Bare `.` is not blocked; `..` is.** `rm -rf .` inside a build or scratch directory is a real
  idiom. `rm -rf ..` never is.

The credential clause is also narrower than the redirection rule's, which blocks writes into *any*
`$HOME` dotfile. Blocking `rm ~/.cache/foo` would be pure friction, so `rm` floors only the three
credential directories.

## Adding a new global hook

1. Write the script and place it in `config/hooks/`
2. Wire it in `config/settings.json` under `hooks.PreToolUse` or `hooks.PostToolUse`
3. Add cases to `tests/bash-guard-cases.txt` — a command it must block, and a similar one it
   must let through — and run `bin/test-hooks`
4. Run `bin/sync-config push` to apply

Both regressions these hooks have had were false positives on the **allow** side, so the
let-through case matters at least as much as the block case:

- `git-guard.sh` matched `.git/` anywhere in the command text, blocking the ordinary idiom
  `find . -not -path "./.git/*"`. It was deleted.
- `bash-guard.sh` matched redirection operators inside quoted strings, so
  `git commit -m "docs: echo x >> ~/.bashrc is blocked"` was blocked — a false positive that
  fires exactly when writing about the rules. Fixed by matching command words against a mask
  with quoted spans blanked out, while still reading arguments from the original text.
- `bash-guard.sh` read comment text as commands, so `echo hi # cat ~/.ssh/id_rsa` was blocked.
  Same shape as the one above, and it hit all five rules. Fixed by blanking a word-initial `#` to
  end of line in the same mask. A mid-word `#` is untouched, so a URL fragment still parses.
- `bash-guard.sh` rule 5 ended an `rm` only on a *standalone* separator token, so a `;` glued to
  the previous word — `rm -rf ./build;ls /` — left the scanner reading the next command's
  arguments as `rm` targets. Fixed by spacing separators out before splitting into words. The
  spaced form `rm -rf ./build ; ls /` always worked, which is what hid it.

## Why capabilities arrive as CLI skills, not MCP servers

An MCP server sends every enabled tool's name, description and full JSON parameter schema to the
model on **every request**, before you have typed anything. A skill sends only its frontmatter
description until the model decides it is relevant. For a capability used occasionally, that
difference dominates.

`zotero-mcp` publishes its own measurement, and it is the clearest available statement of the
trade-off:

| Route | Tokens in context | Paid |
|---|---:|---|
| MCP, default profile (38 tools) | 13,448 | every request |
| MCP, `ZOTERO_MCP_TOOLSETS=none` (32 tools) | 11,761 | every request |
| MCP, `ZOTERO_MCP_TOOLSETS=all` (50 tools) | 17,414 | every request |
| CLI skill, frontmatter only | 98 | always |
| CLI skill, body loaded | 1,368 | once the skill fires |

`ZOTERO_MCP_TOOLSETS` only toggles *optional* groups — the ~32 core tools cannot be trimmed, so
the floor is 11,761 tokens on every turn.

**The rule for this config:** if a capability ships both an MCP server and a CLI, take the CLI and
write (or generate) a skill around it. Reach for an MCP server only when it offers something a CLI
genuinely cannot — a live connection, a stateful session, or a resource the model must be able to
subscribe to. `code-review-graph` is the current exception, and it earns it: it is queried
constantly during ordinary work, so its schemas are not idle weight.

That is the fixed cost only. It says nothing about task success or round trips — a cheaper surface
that gets the answer wrong is not cheaper.

## Setting up Zotero on a new machine

`zotero-mcp-server` is in `config/tools/python-tools.txt`, so `bin/rebuild-tools` installs the
`zotero-cli` and `zotero-mcp` binaries. Two manual steps remain:

1. **Generate the skill.** It is not tracked here (see "What's NOT tracked"):

   ```bash
   zotero-mcp install-skill --list-targets      # confirm the target name
   zotero-mcp install-skill --target claude-user
   ```

   Use `--target claude-user` explicitly. Bare `install-skill` installs into *every* detected
   harness, which in a repo means a project-scoped copy in `.claude/skills/` as well.

2. **Enable Zotero's local API.** In Zotero desktop: Settings → Advanced → "Allow other
   applications on this computer to communicate with Zotero". Without it, `zotero-cli` fails with
   `Local API is not enabled` even though Zotero is running and its connector port answers.

`settings.json` sets `ZOTERO_LOCAL=true`, which is read-only and needs no credentials — that is
why it is safe to keep in the tracked config. Do **not** add `ZOTERO_API_KEY` here; it is a secret
and belongs in `~/.claude/settings.local.json` or your shell rc. Adding it also converts the
library from read-only to writable, which the allow-list below is not sized for.

### The zotero-cli allow-list is scoped to read-only

`settings.json` allow-lists only read subcommands: `search`/`s`, `get`/`g`,
`collections`/`coll`, `annotations list`/`ann list`, `notes list`/`n list`, `outline`, `read`,
`path`, `coverage`. Everything else prompts.

Deliberately excluded, and worth not "tidying up" later:

- `tags` — despite the name it is **`Batch update tags on matched items`**, a write.
- `add`, `edit`, `delete`, `attach`, `batch`, `duplicates` (merges), `library` (switches library).
- `export` — writes files, which would route around `Write`/`Edit` sitting in `ask`.
- `config` — **prints `OPENAI_API_KEY` in full plaintext.** It masks `ZOTERO_LIBRARY_ID` with `*`
  but not the OpenAI key, so an allow-listed `zotero-cli config` would splash a live credential
  into the transcript unprompted. The generated skill suggests running it as a setup check; let it
  prompt, or run `zotero-cli config | grep -v OPENAI` yourself.

These are inert while `ZOTERO_LOCAL=true`, but allow-listing them would become a live write
capability the moment an API key ever enters the environment. Keep the allow-list matched to the
read-only guarantee, not to today's configuration.

## Setting up opencite on a new machine

`opencite[pdf]` is in `config/tools/python-tools.txt`, so `bin/rebuild-tools` installs the
`opencite` binary. It is consumed as a marketplace plugin, not a tracked skill:

```bash
claude plugin marketplace add neuromechanist/research-skills
claude plugin install opencite@research-skills
```

Both are already recorded in the tracked `settings.json` (`extraKnownMarketplaces.research-skills`
and `enabledPlugins`), so on a machine bootstrapped with `bin/sync-config push` Claude resolves
them itself. The marketplace also carries `manuscript`, `figures`, `grant`, `project`,
`neuroinformatics`, `presentation` and `ml-training`. Registering it only makes those installable;
none are enabled.

### System prerequisite

`markit-mistral` pulls `python-magic`, which binds `libmagic` — a system library, not a wheel.
Present on Ubuntu via the `file` package; check with `ldconfig -p | grep libmagic` before
concluding a conversion failure is an opencite bug.

### API keys

**No key is required to use opencite.** It was verified working on 2026-09-03 with none of these
set — `opencite search --source openalex` returned results unauthenticated, contradicting the
upstream skill's `references/api-keys-and-config.md`, which lists `OPENALEX_API_KEY` as "required
since Feb 2026". Treat every key below as a rate-limit upgrade, not an entry ticket.

| Variable | Effect |
|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | The one worth getting, and free. Not a higher limit — a *dedicated* one: unauthenticated callers share a single 1000 req/sec pool globally, so throughput depends on everyone else's traffic. A plain `opencite search` here exhausted 3 retries and dropped the s2 source entirely. A key gives you 1 RPS that is yours |
| `PUBMED_API_KEY` | Free, instant from an NCBI account. Raises E-utilities from 3 to 10 req/sec |
| `OPENALEX_API_KEY` | Not needed — works unauthenticated. Only for the paid premium pool |
| `MISTRAL_API_KEY` | Switches PDF→markdown from markitdown to markit-mistral (math, tables, image extraction) |
| `CORE_API_KEY` | Free from core.ac.uk. Adds the CORE aggregator as a source |
| `OPENCITE_ELSEVIER_KEY`, `OPENCITE_WILEY_TDM_TOKEN`, `OPENCITE_SPRINGER_KEY` | Authenticated publisher PDFs. **Note the `OPENCITE_` prefix** — see below |

#### Upstream documents the publisher variables under the wrong names

opencite's own README and the skill's `references/api-keys-and-config.md` both say to export
`ELSEVIER_API_KEY`, `WILEY_TDM_TOKEN` and `SPRINGER_API_KEY`. Those names appear nowhere in the
package. `config.py`'s `_TOML_MAP` reads `OPENCITE_ELSEVIER_KEY`, `OPENCITE_WILEY_TDM_TOKEN` and
`OPENCITE_SPRINGER_KEY`. Setting the documented names does nothing, silently — you get
open-access fallback and no error. Use the TOML file instead of environment variables for these;
the `[publishers]` keys (`elsevier`, `wiley_tdm`, `springer`) are unambiguous and correct in both.

The four `[api_keys]` variables are not affected: `SEMANTIC_SCHOLAR_API_KEY`, `PUBMED_API_KEY`,
`OPENALEX_API_KEY` and `MISTRAL_API_KEY` are read under exactly those names.

#### Where to put them

The file does not exist until you create it:

```bash
opencite config init            # writes ~/.opencite/config.toml from a template
chmod 600 ~/.opencite/config.toml   # it does NOT do this for you — created 0644
```

Then fill in the `[api_keys]` and `[publishers]` blocks. All of these are secrets, so they belong
there or in `~/.claude/settings.local.json` — **never** the tracked `settings.json`, the same rule
that keeps `ZOTERO_API_KEY` out of it. `ZOTERO_LOCAL=true` is in the tracked `env` block only
because it is not a credential.

`~/.opencite/config.toml` is the *lowest*-priority source: `~/.opencite/.env`, a `.env` in the
working directory, and then real environment variables all override it. A stale export in your
shell rc silently wins over the file you just edited.

#### Three settings worth knowing about

- `settings.contact_email` (`OPENCITE_EMAIL`) — not a credential. It puts you in OpenAlex's and
  Crossref's "polite pool", which is the actual reason keyless OpenAlex works well. Set it first;
  it costs nothing.
- `settings.disabled_sources` (`OPENCITE_DISABLED_SOURCES`) — comma-separated sources to skip.
  `"osf"` silences the HTTP 400 warning noted below; `"s2"` is the documented escape hatch if you
  never get a Semantic Scholar key and the retry stalls annoy you.
- `defaults.max_results` / `format` / `converter` — defaults so you stop passing `--max` and `-f`.

Two warnings are normal on a keyless run and are not wiring faults: `Rate limited by
api.semanticscholar.org` (add the S2 key to stop it) and `OSF search failed … HTTP 400`, an
upstream query-encoding bug in opencite's OSF client. Results still come back from the remaining
sources in both cases.

#### CORE is broken upstream even with a valid key

`--source core` returns zero results and logs `HTTP 301: Redirect response … Moved Permanently`.
This is **not** a bad key. Verified 2026-09-03: the same key against
`https://api.core.ac.uk/v3/search/works/` returns HTTP 200 and a full result set, while a
deliberately wrong key returns 401.

Two upstream defects combine. `clients/core.py:66` requests `/v3/search/works` without the
trailing slash CORE now redirects to, and `clients/base.py:123` builds its `httpx.AsyncClient`
without `follow_redirects=True` — httpx defaults that to `False`, so the 301 is never followed.
Either fix alone resolves it.

Until it is fixed upstream, add `core` to `disabled_sources` to stop the warning on every
`--source all` search. Keep the key in the config; it will start working the moment opencite is
patched.

#### Verifying a key without pasting it anywhere

`opencite config show` masks to first-and-last-four, so it confirms a key is *loaded*, not that it
is *accepted*. To check acceptance, probe the source directly and read only the status code —
distinguishing rejection from throttling matters:

| Source | Valid | Invalid |
|---|---|---|
| Semantic Scholar | 200, or **429 when throttled** | **403** |
| NCBI E-utilities | 200 | 400 |
| CORE | 200 | 401 |

S2's 429 is the one to know: it means the key was accepted and you hit your dedicated 1 RPS, not
that it was refused. Wait a few seconds and re-probe rather than concluding the key is bad.

### `mistralai` is pinned below 2.0

`markit-mistral` 0.2.3 requires `mistralai>=1.0.0` with no upper bound but imports
`DocumentURLChunk`, which mistralai 2.x removed. opencite imports markit-mistral lazily and only
when `MISTRAL_API_KEY` is set, so an unconstrained resolve leaves an `ImportError` that stays
invisible until the day a Mistral key is added. `mistralai<2` therefore sits in
`python-tools.txt` as a constraint rather than a tool — the one entry there that is not itself a
binary. Drop it once markit-mistral supports mistralai 2.x.

### Retrieved PDFs carry a license sidecar

Every download writes `<pdf>.license.json` beside the PDF, recording `{url, source, license,
version, oa_status, publisher_tdm, doi, retrieved_at}`. opencite does not enforce a redistribution
policy — it reports and leaves the call to you. If retrieved PDFs or their markdown ever land in a
repo, that sidecar is the machine-readable "safe to commit?" signal: `publisher_tdm: true` marks
bytes obtained through an Elsevier/Wiley/Springer TDM token, which those agreements almost
universally forbid redistributing. Note that `oa_status: bronze` is free to read but *not* openly
licensed, a distinction `is_oa` collapses.

### The opencite allow-list cannot be read-only

`settings.json` allow-lists `search`, `lookup`, `cite`, `canonical` and `ids`. Unlike the
`zotero-cli` list above, **this one is not a read-only guarantee, and should not be described as
one**: every one of those subcommands accepts `-o FILE`, and permission patterns are prefix globs
with no way to express "not containing `-o`". `Bash(opencite search *)` therefore permits a file
write.

That is accepted deliberately. A query verb writes only its own bounded, self-generated text — the
result set it just printed — to a path the caller named, and producing `results.json` for
`batch-fetch` is the documented workflow. The line is drawn at commands that write *arbitrary
remote bytes*:

- `pdf`, `convert`, `batch-fetch` — download and materialise publisher content. Left on prompt for
  the same reason `zotero-cli export` is excluded above.
- `config` — `config init` writes `~/.opencite/config.toml`, which is the reason it stays on
  prompt. Not for the `zotero-cli` reason, though: opencite's masking was **verified on
  2026-09-03** against a live value and it does mask, showing only the first and last four
  characters (`DUMM...7890`). `opencite config show` is safe to run and to paste; `zotero-cli
  config` still is not.

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
