# scripts/

Executable scripts that Claude runs during skill execution.

Bundling logic here means every invocation reuses the same script rather than
re-implementing it from scratch. Useful for:

- File format conversions (e.g. `build_docx.py`, `render_chart.py`)
- Data transformations that require deterministic behavior
- Setup or validation steps that are the same across inputs

Reference scripts from `SKILL.md` with a clear note on when to run them:

```markdown
Run `python ${CLAUDE_PLUGIN_ROOT}/skills/SKILL_NAME/scripts/your_script.py`
to [do X]. Pass the output path as the first argument.
```

Delete this directory if the skill has no bundled scripts.
