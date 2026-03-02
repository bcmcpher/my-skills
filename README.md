# Claude Code Skills, Agents & Plugins

Personal monorepo for developing Claude Code plugins — skills (slash commands), subagents,
hooks, and MCP server configs. Each plugin under `plugins/` is independently installable.

---

## Installation

```bash
# Test locally during development (session-only)
claude --plugin-dir ./plugins/<name>

# Install permanently (user scope)
claude plugin install ./plugins/<name>

# Install from GitHub (when a plugin has its own repo)
claude plugin install https://github.com/bcmcpher/<plugin-name>
```

---

## Plugins

| Plugin | Description |
|--------|-------------|
| [example-hello](./plugins/example-hello/) | Working example: `/hello` skill + greeter subagent |

---

## Templates

Start new tools by copying a template:

```bash
cp -r templates/skill  plugins/my-new-skill
cp -r templates/agent  plugins/my-new-agent
cp -r templates/plugin plugins/my-new-plugin
```

Then replace all `PLUGIN_NAME`, `SKILL_NAME`, `AGENT_NAME` placeholders with real names.
Each template includes a `SETUP.md` with detailed setup instructions — it's the first thing to read after copying and the last thing to replace with your own `README.md`.

| Template | Use when |
|----------|----------|
| [templates/skill/](./templates/skill/) | Adding a slash command or auto-invoked instruction |
| [templates/agent/](./templates/agent/) | Adding a specialized subagent with isolated context |
| [templates/plugin/](./templates/plugin/) | Full plugin: skills + agents + hooks + MCP server |

---

## Creating a new plugin

### 1. Choose a template

| If you want… | Use |
|---|---|
| A slash command or auto-triggered instruction set | `templates/skill` |
| A specialized subagent with its own context and policy | `templates/agent` |
| Both, plus hooks or MCP servers | `templates/plugin` |

Start with the smallest template that covers your need. You can always promote a skill to a full plugin later.

### 2. Copy and rename

```bash
cp -r templates/skill  plugins/my-new-skill   # or agent / plugin
```

Then rename the placeholder directories inside:

```bash
mv plugins/my-new-skill/skills/SKILL_NAME  plugins/my-new-skill/skills/my-new-skill
```

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

```bash
claude plugin install ./plugins/my-new-skill
```

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
├── .gitignore
├── templates/
│   ├── skill/               # Pure skill template
│   │   ├── SETUP.md         # Setup guide (replace with README.md when done)
│   │   └── skills/SKILL_NAME/
│   │       ├── SKILL.md
│   │       ├── scripts/     # Helper scripts bundled with the skill
│   │       ├── references/  # Reference docs loaded on demand
│   │       └── assets/      # Static files used in output
│   ├── agent/               # Custom subagent template
│   │   ├── SETUP.md
│   │   └── agents/AGENT_NAME/
│   │       ├── SKILL.md
│   │       ├── scripts/
│   │       ├── references/
│   │       └── assets/
│   └── plugin/              # Full plugin template (skills + agents + hooks + MCP)
│       ├── SETUP.md
│       ├── hooks/
│       │   └── hooks.json.example   # Activate by copying to hooks.json
│       └── .mcp.json
└── plugins/
    └── example-hello/       # Working example plugin
```
