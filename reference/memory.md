# Claude Code Memory Reference

Claude Code has three distinct memory mechanisms. Use the right one for the right scope.

---

## 1. CLAUDE.md — project instructions

The primary mechanism. Claude reads `CLAUDE.md` from the **project root** and any
**ancestor directories** up to the filesystem root (e.g., `~/CLAUDE.md` applies globally).

**Key limits and behaviors:**

- Claude reads the file at session start; changes mid-session require a restart or `/reload`
- Keep the file **under ~200 lines** — content after that may be truncated
- Use `<important>` tags to flag critical instructions Claude must not ignore:
  ```markdown
  <important>Never edit files outside the src/ directory without confirmation.</important>
  ```
- Descendant `CLAUDE.md` files (subdirs) are also loaded and scoped to that subtree

### What to put in CLAUDE.md

- Project type, language, architecture overview
- Common commands (`build`, `test`, `lint`)
- Conventions (naming, commit message style, branch strategy)
- What Claude should never do in this project
- Pointers to reference files for deeper context

### What not to put in CLAUDE.md

- Secrets or credentials
- Things that change per-session (put those in the chat)
- Duplicated content that's already obvious from the code

---

## 2. `.claude/rules/` — split CLAUDE.md into multiple files

When `CLAUDE.md` exceeds ~100 lines, split domain-specific instructions into separate files
under `.claude/rules/`. Claude loads all files in that directory automatically.

```
.claude/
├── rules/
│   ├── git.md          # git workflow rules
│   ├── testing.md      # test conventions
│   └── data.md         # data handling rules
```

Each file follows the same format as `CLAUDE.md` (plain markdown, no frontmatter needed).

### @path imports

You can import another file into `CLAUDE.md` using `@path`:

```markdown
## Git workflow
@.claude/rules/git.md

## Testing
@.claude/rules/testing.md
```

This keeps the root `CLAUDE.md` as a table of contents and avoids the 200-line limit.

---

## 3. Auto-memory — cross-session persistence (Claude's own notes)

Claude maintains a persistent memory file at:

```
~/.claude/projects/<encoded-path>/memory/
```

This is Claude's scratchpad across sessions — not project instructions, but notes Claude
writes to itself (user preferences, project context, decisions made). It is private to
Claude and not committed to the repo.

**You can ask Claude to remember things:** "Remember that we use `pytest -x` not `pytest`
for this project." Claude will write a memory file entry.

**You can ask Claude to forget things:** "Forget that note about the old API."

Auto-memory is distinct from CLAUDE.md:
- `CLAUDE.md` = your instructions to Claude (you write it)
- Auto-memory = Claude's notes to itself (Claude writes it, you can inspect/direct it)

---

## Choosing the right mechanism

| Use case | Mechanism |
|---|---|
| Project conventions, architecture, commands | `CLAUDE.md` |
| Domain-specific rules (large projects) | `.claude/rules/*.md` |
| User preferences, cross-project patterns | `~/.claude/CLAUDE.md` (global) |
| Session-to-session personal notes | Auto-memory |
| Secrets / credentials | Never in memory — use env vars |
