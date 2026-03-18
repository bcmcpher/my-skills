# Skill Template — Setup Guide

> This file is a setup reference. Replace it with your plugin's `README.md` when done.

Copy this directory to `plugins/my-git-workflow`, then:

1. Rename `skills/git-workflow/` to `skills/your-git-workflow/`
2. Edit `.claude-plugin/plugin.json` — replace `git-workflow`, `git-workflow`, `DESCRIPTION`
3. Edit `skills/your-git-workflow/SKILL.md` — fill in frontmatter and body
4. Replace this file (`SETUP.md`) with your plugin's `README.md`
5. Delete unused resource subdirectories (`scripts/`, `references/`, `assets/`)
6. Test: `claude --plugin-dir ./plugins/my-git-workflow`
7. Invoke: `/your-git-workflow` in the Claude Code session

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

## Bundling resources

Each skill directory supports three optional subdirectories alongside `SKILL.md`:

```
skills/your-git-workflow/
├── SKILL.md
├── scripts/      # Helper scripts Claude executes (avoids re-implementing logic per invocation)
├── references/   # Reference docs loaded into context on demand (keeps SKILL.md concise)
└── assets/       # Static files used in output (templates, fonts, icons)
```

**`scripts/`** — Put deterministic helper logic here. If every invocation would otherwise re-write the same Python/JS, bundle it as a script and reference it from `SKILL.md`:
```markdown
Run `python ${CLAUDE_PLUGIN_ROOT}/skills/your-skill/scripts/build_report.py <output_path>`.
```

**`references/`** — Move large lookup tables, API specs, or style guides here. Claude reads them on demand rather than loading them in context permanently. For files over 300 lines, add a table of contents at the top.

**`assets/`** — Templates, logos, fonts, or any static file the skill embeds in its output.

Delete any subdirectory you don't use — empty directories add no value.

---

## Testing

Tight iteration loop:

1. Load the plugin: `claude --plugin-dir ./plugins/my-git-workflow`
2. Invoke the skill: type `/your-git-workflow` (with arguments if needed)
3. Check the output — does it match what you intended?
4. Edit `skills/your-git-workflow/SKILL.md`
5. Exit the session and reload from step 1

Repeat until the output is consistently correct. Once stable, install permanently:

```bash
claude plugin install ./plugins/my-git-workflow
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
