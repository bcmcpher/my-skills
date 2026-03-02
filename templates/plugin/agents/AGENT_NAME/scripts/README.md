# scripts/

Executable scripts that the agent runs during its work.

Bundling logic here means every invocation reuses the same script rather than
re-implementing it from scratch. Useful for:

- Data processing or transformation steps
- Validation or scoring scripts
- Setup steps that are identical across inputs

Reference scripts from `SKILL.md` with a clear note on when to run them:

```markdown
Run `python ${CLAUDE_PLUGIN_ROOT}/agents/AGENT_NAME/scripts/your_script.py`
to [do X].
```

Delete this directory if the agent has no bundled scripts.
