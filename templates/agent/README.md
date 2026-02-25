# Agent Template

Copy this directory to `plugins/my-agent-name`, then:

1. Rename `agents/AGENT_NAME/` to `agents/your-agent-name/`
2. Edit `.claude-plugin/plugin.json` — replace `PLUGIN_NAME`, `AGENT_NAME`, `DESCRIPTION`
3. Edit `agents/your-agent-name/SKILL.md` — fill in frontmatter and system prompt body
4. Test: `claude --plugin-dir ./plugins/my-agent-name`
5. In a session, describe a task that matches the agent's description and confirm delegation fires

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
