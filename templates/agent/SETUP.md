# Agent Template — Setup Guide

> This file is a setup reference. Replace it with your plugin's `README.md` when done.

Copy this directory to `plugins/my-agent-name`, then:

1. Rename `agents/AGENT_NAME/` to `agents/your-agent-name/`
2. Edit `.claude-plugin/plugin.json` — replace `PLUGIN_NAME`, `AGENT_NAME`, `DESCRIPTION`
3. Edit `agents/your-agent-name/SKILL.md` — fill in frontmatter and system prompt body
4. Replace this file (`SETUP.md`) with your plugin's `README.md`
5. Delete unused resource subdirectories (`scripts/`, `references/`, `assets/`)
6. Test: `claude --plugin-dir ./plugins/my-agent-name`
7. In a session, describe a task that matches the agent's description and confirm delegation fires

---

## Writing a good description

The `description` field is a **delegation trigger** — the main Claude reads it to decide whether to hand off work to this agent. It must describe *when* to delegate, not just *what* the agent does.

- Good: `"Delegate when the user asks for encouragement, a pep talk, or says they're feeling stuck or frustrated"`
- Bad: `"An encouraging assistant that provides motivation"`

The "bad" example describes the agent's personality. The "good" example tells the main Claude the exact conditions under which to delegate. Without a precise trigger, the agent never fires (or fires for everything).

---

## Writing the system prompt

The body of `SKILL.md` is the agent's system prompt. Structure it as a policy document:

1. **Purpose statement** — first sentence states exactly what this agent does
2. **Steps** — numbered list of what the agent does when invoked
3. **Hard constraints** — `Always:` / `Never:` lines at the end

Example structure:

```
You are a code-review agent. Your job is to review the diff provided and give structured feedback.

1. Read the full diff before commenting.
2. Identify issues by severity: blocking, suggestion, or nit.
3. Group comments by file.
4. End with a one-sentence overall assessment.

Always stay focused on the code; never comment on commit message style.
Never approve changes that introduce obvious security vulnerabilities.
```

The agent runs in an isolated context — it does not inherit the parent conversation. Make the system prompt self-contained.

---

## Bundling resources

Each agent directory supports three optional subdirectories alongside `SKILL.md`:

```
agents/your-agent-name/
├── SKILL.md
├── scripts/      # Helper scripts the agent executes
├── references/   # Reference docs loaded into context on demand
└── assets/       # Static files the agent uses in its output
```

**`scripts/`** — Logic the agent would otherwise re-implement each run. Bundle it once, reference from `SKILL.md`:
```markdown
Run `python ${CLAUDE_PLUGIN_ROOT}/agents/your-agent/scripts/process.py`.
```

**`references/`** — Policies, specs, or background context too large to keep in the system prompt. Claude reads them when needed. Add a table of contents for files over 300 lines.

**`assets/`** — Output templates or static files the agent embeds in its responses.

Delete any subdirectory you don't use.

---

## Testing

1. Load the plugin: `claude --plugin-dir ./plugins/my-agent-name`
2. In the session, describe a task that matches the agent's description (don't just say "delegate to X")
3. Confirm that the main Claude delegates — look for the subagent being invoked in the output
4. Check that the agent's response follows the system prompt policy
5. Edit `agents/your-agent-name/SKILL.md` and reload to iterate

If delegation never fires, tighten the `description` to be more specific about the trigger condition.

Once stable, install permanently:

```bash
claude plugin install ./plugins/my-agent-name
```

## Frontmatter fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Slug identifying this agent |
| `description` | yes | When should the main Claude delegate here? Be precise. |
| `tools` | no | Comma-separated tools the subagent can use |
| `model` | no | `inherit` (default) or a specific model ID |
| `permissionMode` | no | `default`, `acceptEdits`, or `bypassPermissions` |
| `maxTurns` | no | Maximum agentic turns before stopping |
