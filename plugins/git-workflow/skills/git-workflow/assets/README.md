# assets/

Static files used in skill output — templates, fonts, icons, images, etc.

Examples:
- A `.docx` or `.pptx` template the skill populates
- A logo or icon embedded in generated files
- A font file required for PDF rendering

Reference from `SKILL.md` with the path via `${CLAUDE_PLUGIN_ROOT}`:

```markdown
Use the template at `${CLAUDE_PLUGIN_ROOT}/skills/git-workflow/assets/template.docx`
as the base document.
```

Delete this directory if the skill produces no file output.
