# Writing style for documentation

The fallback style for technical documentation written to disk: READMEs, guides, user-facing
notes. It is based on ASD-STE100 Simplified Technical English, applied at about 80% — follow the
rules where they help clarity; do not contort text to satisfy them.

It does not apply to:

- conversation replies — the active output style (e.g. caveman) governs those;
- spec artifacts — the spec tool's own rules govern those (see `specs.md`);
- manuscripts, grant text and other scientific prose;
- any project that sets its own documentation style.

## Rules

- One topic per sentence. Procedural sentences: 20 words or fewer. Descriptive: 25 or fewer.
- Use the active voice.
- Write instructions in the imperative, one instruction per sentence. Put steps in a numbered
  list.
- Keep paragraphs to six sentences or fewer.
- Prefer simple verbs to phrasal verbs and to -ing nouns ("set up" → "configure").
- State facts plainly. Do not hedge.

## Technical terms

Use one term for one concept, and keep it.

- Define a technical term in-line where it first appears.
- Also record it in the project glossary (`GLOSSARY.md`, `docs/glossary.md`, or a "Key terms"
  section). The glossary is the authority on what a term means.
- If there is no glossary and project-specific terms accumulate, offer to create one.
- After a term is defined, do not substitute a synonym for it.
