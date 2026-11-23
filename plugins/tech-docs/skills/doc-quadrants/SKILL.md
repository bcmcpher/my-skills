---
name: doc-quadrants
description: Classify documentation by the four documentation quadrants (Diátaxis) — tutorial, how-to guide, reference, explanation — label each section with its quadrant and evidence, flag sections that mix two quadrants, propose a file split with a landing page, or audit a docs directory for missing quadrants. Use when the user asks to classify a doc by type, check whether a README mixes tutorials and reference, split a document by the Diátaxis or documentation-quadrants model, or audit a doc set for gaps.
argument-hint: [classify|split|audit] <file or directory>
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob
---

# Skill: doc-quadrants

Classify documentation by the four documentation quadrants. `$ARGUMENTS` names the mode and
the target. With no mode, use **classify** for a file and **audit** for a directory.
`<refs>` is `${CLAUDE_PLUGIN_ROOT}/skills/doc-quadrants/references`.

Read `<refs>/quadrants.md` first. It defines the quadrants, their signals and the mixed cases.
Call the fourth quadrant **Explanation**, never "Discussion".

## Modes

### classify

1. Read the target file. Split it into sections at its headings. A section with no heading is
   the text before the first heading.
2. Give each section one label: Tutorial, How-to guide, Reference, Explanation, or **mixed**
   with the two quadrants it collapses. Front matter, badges and a one-line summary are
   **landing** content; do not label them.
3. For each label, give one line of evidence from the section: a phrase, a structure (numbered
   steps, an option table), or what the section assumes the reader knows.
4. Output a table: section heading, label, evidence. Under it, list the mixed sections with the
   part of each that belongs to the other quadrant.

### split

1. Run **classify** first and show its table.
2. Propose a file plan in `<refs>/quadrants.md` style:
   - the new file names (how-to files named by task, such as `how-to-validate-input.md`);
   - which sections, or parts of mixed sections, move to each file;
   - the landing page: what stays in the original file, plus one routing line per new file.
3. Move content whole in the plan. Do not rewrite it in the same step.
4. Stop. This is a proposal. Edit or create no file until the user approves the plan.

### audit

1. List the Markdown files in the directory (`**/*.md`). Leave out vendored and generated trees.
2. Classify each file at file level: its main quadrant, or mixed. Read only as much of each file
   as the label needs.
3. Report the quadrants that exist (with their files), the quadrants that are missing, and the
   mixed files. For each mixed file, name the sections that cause the mix.
4. Recommend the next step for the largest gap. That is a missing quadrant, or the mixed file
   that most readers meet first (usually the README).

## Constraints

- Read-only. This skill never edits files. A split happens only after the user approves it,
  and then the `technical-docs-writer` agent or the user does the edit.
- A short README can hold all four quadrants in separate sections. Flag a section as mixed only
  when two quadrants share one section.
- Label by what a section does for the reader, not by its heading text.
