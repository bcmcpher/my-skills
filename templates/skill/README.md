# Skill Template

Copy this directory to `plugins/my-skill-name`, then:

1. Rename `skills/SKILL_NAME/` to `skills/your-skill-name/`
2. Edit `.claude-plugin/plugin.json` — replace `PLUGIN_NAME`, `SKILL_NAME`, `DESCRIPTION`
3. Edit `skills/your-skill-name/SKILL.md` — fill in frontmatter and body
4. Test: `claude --plugin-dir ./plugins/my-skill-name`
5. Invoke: `/your-skill-name` in the Claude Code session

---

## Choosing a name and description

**`name`** becomes the slash command slug. Keep it short and memorable — one or two words, no spaces.
`name: commit-msg` → `/commit-msg`. Users will type this; make it obvious.

**`description`** is the sentence Claude reads to decide whether to auto-invoke the skill. It should answer: *under what specific condition should this run, and what does it produce?*

- Good: `"When the user asks to generate a commit message, produce a conventional-commits formatted message from staged changes"`
- Bad: `"Helps with commits"`

A vague description causes the skill to fire too broadly or not at all. A precise description makes auto-invocation reliable.

---

## Writing the instructions body

Use imperative prose — tell Claude what to do, not what the skill is.

Structure the body as:
1. A brief purpose statement (one sentence)
2. Numbered steps Claude should follow
3. Constraints at the end (what to avoid, what format to produce)

If the skill accepts input, reference `$ARGUMENTS` where the user's text should be substituted.

Example structure:

```
Generate a conventional-commits message for the current staged diff.

1. Run `git diff --cached` to read the staged changes.
2. Identify the change type (feat, fix, chore, docs, refactor, etc.).
3. Write a subject line under 72 characters: `<type>(<scope>): <summary>`
4. Add a body if the change is non-trivial.

Never invent details not present in the diff.
Output only the commit message — no commentary.
```

---

## Testing

Tight iteration loop:

1. Load the plugin: `claude --plugin-dir ./plugins/my-skill-name`
2. Invoke the skill: type `/your-skill-name` (with arguments if needed)
3. Check the output — does it match what you intended?
4. Edit `skills/your-skill-name/SKILL.md`
5. Exit the session and reload from step 1

Repeat until the output is consistently correct. Once stable, install permanently:

```bash
claude plugin install ./plugins/my-skill-name
```

## Frontmatter fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Slug used as the slash command (e.g. `hello` → `/hello`) |
| `description` | yes | Used by Claude to decide when to auto-invoke. Be specific. |
| `argument-hint` | no | Shown in the autocomplete UI |
| `user-invocable` | no | `true` = appears as `/name` slash command |
| `disable-model-invocation` | no | `true` = run as a hook, not an LLM call |
| `allowed-tools` | no | Comma-separated list of tools the skill may use |
