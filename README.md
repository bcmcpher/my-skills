# Claude Code Skills, Agents & Plugins

Personal monorepo for developing Claude Code plugins — skills (slash commands), subagents,
hooks, and MCP server configs. Each plugin under `plugins/` is independently installable.

---

## Installation

Plugins install through a **marketplace**, not a bare path. This repo ships one
(`.claude-plugin/marketplace.json`, named `local`), so register it once and then install any
plugin by name:

```bash
# Test locally during development (session-only, no install)
claude --plugin-dir ./plugins/<name>

# Install permanently (user scope):
claude plugin marketplace add .          # once, from the repo root (a GitHub URL also works)
claude plugin install <name>@local       # then restart Claude Code to load it
```

> `claude plugin install ./plugins/<name>` does **not** work — `install` resolves plugins from
> configured marketplaces, so the `<name>@local` form is required. Update the marketplace later
> with `claude plugin marketplace update local`.

Once a plugin graduates to its own repo you can add it as a standalone marketplace:
`claude plugin marketplace add bcmcpher/<plugin-name>`.

---

## Plugins

| Plugin | Description |
|--------|-------------|
| [bids](./plugins/bids/) | BIDS (Brain Imaging Data Structure) conventions and dataset validation for neuroimaging data |
| [boutiques](./plugins/boutiques/) | `/boutiques <cmd> [subcmd]` — generate a Boutiques 0.5 JSON descriptor from `--help` output |
| [datalad-cli](./plugins/datalad-cli/) | 20 `datalad-*` skills routing data processing through DataLad for provenance, plus a STAMPED reproducibility assessment |
| [git-workflow](./plugins/git-workflow/) | Git workflow practices and PR lifecycle commands (`/commit`, `/commit-push-pr`, `/review-pr`, `/clean-gone`) |
| [modular-analysis](./plugins/modular-analysis/) | `/analysis-plan` and `/analysis-refactor` — structure repeated analyses around a five-layer architecture |
| [nipoppy-cli](./plugins/nipoppy-cli/) | Skills for the nipoppy neuroimaging pipeline management framework |
| [programming-tools](./plugins/programming-tools/) | `/tdd`, `/retrofit-tests`, `/code-check`, plus six review subagents (code review, simplification, silent failures, type design, comments, PR tests) |
| [project-init](./plugins/project-init/) | Scaffold and configure new projects across coding-tool, data-analysis, and info-management types |
| [stat-analysis](./plugins/stat-analysis/) | Merge input data, plan the right statistical test with QC checks, and scaffold a jupytext report |

Every plugin is listed in [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json);
`bin/validate` fails if that file and `plugins/` disagree.

---

## Templates

Start new tools by copying a template:

```bash
bin/new-plugin skill  my-new-skill      # or: agent | hook | mcp
```

`bin/new-plugin` copies the chosen template, renames the placeholder directories, and replaces
the `PLUGIN_NAME` / `SKILL_NAME` / `AGENT_NAME` tokens for you. Copying by hand works too
(`cp -r templates/skill plugins/my-new-skill`), but then the renaming is yours to do.

| Template | Use when |
|----------|----------|
| [templates/skill/](./templates/skill/) | Adding a slash command or auto-invoked instruction |
| [templates/agent/](./templates/agent/) | Adding a specialized subagent with isolated context |
| [templates/hooks/](./templates/hooks/) | Adding PreToolUse / PostToolUse / Stop hooks to a plugin |
| [templates/mcp/](./templates/mcp/) | Adding MCP server stubs (Python, TypeScript, Docker) to a plugin |

The `skill` and `agent` templates each ship a `SETUP.md` — the first thing to read after copying,
and the last thing to replace with your own `README.md`. `bin/graduate <name>` checks that you did.

For a full plugin combining skills, agents, hooks and MCP, use [`reference/plugin/`](./reference/plugin/)
as the structural reference rather than a template.

---

## Creating a new plugin

### 1. Choose a template

| If you want… | Use |
|---|---|
| A slash command or auto-triggered instruction set | `templates/skill` |
| A specialized subagent with its own context and policy | `templates/agent` |
| To add hooks to a plugin you already have | `templates/hooks` |
| To add an MCP server to a plugin you already have | `templates/mcp` |

Start with the smallest template that covers your need — a skill plugin can gain agents, hooks,
or an MCP server later without being rebuilt.

### 2. Scaffold

```bash
bin/new-plugin skill my-new-skill      # type: skill | agent | hook | mcp
```

This copies the template, renames the `SKILL_NAME` / `AGENT_NAME` directories, and substitutes the
`PLUGIN_NAME` / `SKILL_NAME` / `AGENT_NAME` tokens throughout. Doing it by hand is the same work:

```bash
cp -r templates/skill plugins/my-new-skill
mv plugins/my-new-skill/skills/SKILL_NAME plugins/my-new-skill/skills/my-new-skill
```

`bin/new-plugin mcp <name>` scaffolds three parallel server stubs — Python (FastMCP/uv),
TypeScript (MCP SDK/tsx), and Docker — all wired into `.mcp.json`. Delete the ones you will not
use, and remove their entries from `.mcp.json`, before testing.

### 3. Edit the manifest (`plugin.json`)

Open `.claude-plugin/plugin.json` and fill in every placeholder:

- `name` — kebab-case slug, shown in listings and used internally
- `description` — one sentence; what does this plugin do?
- `version` — start at `0.1.0`
- `skills` / `agents` — paths to your SKILL.md directories (update after renaming)

Leave `hooks` and `mcpConfig` out of the manifest entirely if you're not using them.

### 4. Write the SKILL.md

**For skills:** the `description` frontmatter field is what Claude reads to decide when to auto-invoke the skill. Make it specific about the trigger condition and what the skill produces. The `name` field becomes the slash command (`name: commit` → `/commit`).

**For agents:** the `description` field is a delegation trigger — it describes *when* the main Claude should hand off work to this agent. The body of the file is the agent's system prompt; write it as a policy (purpose statement, explicit steps, hard constraints).

### 5. Test locally

```bash
claude --plugin-dir ./plugins/my-new-skill
```

Inside the session, invoke your skill with `/skill-name` or describe a task that should trigger it. Edit `SKILL.md`, exit and relaunch to reload.

### 6. Install permanently

Register this repo's marketplace once, then install the plugin by name:

```bash
claude plugin marketplace add .          # from the repo root
claude plugin install my-new-skill@local # restart Claude Code to load
```

If you already added the marketplace and only changed the plugin, refresh it with
`claude plugin marketplace update local` before installing.

---

## When to graduate a plugin to its own repo

Keep it in this monorepo while:
- Iterating / experimenting
- Using via `--plugin-dir` path or GitHub subpath
- Tool is personal or early-stage

Graduate to a standalone repo when:
- You want semantic versioning and a CHANGELOG
- Publishing to the Claude Code marketplace (marketplace points to a repo URL)
- Plugin has its own tests, CI, or external dependencies
- Others should be able to `claude plugin install github.com/bcmcpher/<name>`

### Graduation checklist

```bash
# 1. Create the new repo and push the plugin contents (not the whole monorepo)
gh repo create bcmcpher/<plugin-name> --public --clone
cp -r plugins/<plugin-name>/. <plugin-name>/
cd <plugin-name> && git add . && git init && git commit -m "initial commit"
git remote add origin https://github.com/bcmcpher/<plugin-name>
git push -u origin main
```

Then in the new repo:

- [ ] **`README.md`** — confirm install instructions point to the new repo URL:
  `claude plugin install https://github.com/bcmcpher/<plugin-name>`
- [ ] **`CHANGELOG.md`** — add an initial entry (`## 0.1.0 — initial release`)
- [ ] **`plugin.json`** — add `"repository"` field:
  `"repository": "https://github.com/bcmcpher/<plugin-name>"`
- [ ] **`plugin.json` version** — bump to `1.0.0` if it's ready for general use
- [ ] **GitHub release** — tag `v1.0.0` (or `v0.1.0`) so the marketplace can resolve a stable version
- [ ] **This monorepo** — update the Plugins table in this README to link to the new repo,
  and optionally replace `plugins/<plugin-name>/` with a note pointing there

Optional but useful:
- [ ] **`.github/workflows/`** — add a CI workflow to lint or test on push
- [ ] **`LICENSE`** — verify it's present (MIT is already in the template)
- [ ] **Topics** — add `claude-code-plugin` to the GitHub repo topics for discoverability

---

## Project structure

```
my-skills/
├── README.md
├── CLAUDE.md                # Guidance for Claude Code working in this repo
├── .claude-plugin/
│   └── marketplace.json     # The `local` marketplace; one entry per plugin
├── bin/                     # Repo tooling
│   ├── new-plugin           # Scaffold a plugin from a template
│   ├── validate             # Manifest + frontmatter + marketplace checks (runs in CI)
│   ├── graduate             # Is this plugin fully converted and publishable?
│   ├── sync-config          # config/ ↔ ~/.claude/
│   ├── rebuild-tools        # Rebuild/verify the harness tool environments
│   └── test-hooks           # Exercise the PreToolUse hooks against tests/
├── config/                  # Global ~/.claude/ config tracked here
│   ├── settings.json        # Enabled plugins, permissions, global hooks wiring
│   ├── hooks/               # Global hook scripts (~/.claude/hooks/)
│   ├── skills/              # Standalone globally-installed skills (~/.claude/skills/)
│   ├── tools/               # Lock files for the harness tool environments
│   └── xdg/                 # Tool configs outside ~/.claude/ (openspec, caveman)
├── plans/                   # Design docs for work not yet built
├── reference/               # Quick reference for skill authors
│   ├── plugin/              # Annotated plugin anatomy, incl. .lsp.json
│   ├── settings.md          # Settings hierarchy, permissions, env vars
│   ├── memory.md            # CLAUDE.md patterns, .claude/rules/, @path imports
│   └── statusline.md        # statusLine config and command contract
├── templates/
│   ├── skill/               # Slash command / auto-invoked instruction only
│   │   ├── SETUP.md         # Setup guide (replace with README.md when done)
│   │   └── skills/SKILL_NAME/
│   ├── agent/               # Custom subagent only
│   │   ├── SETUP.md
│   │   └── agents/AGENT_NAME/
│   ├── hooks/               # PreToolUse / PostToolUse / Stop hook stubs
│   └── mcp/                 # MCP server stubs (Python, TypeScript, Docker)
├── tests/                   # Case table for bin/test-hooks
└── plugins/                 # One directory per installable plugin
```
