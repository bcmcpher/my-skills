# Documentation quadrants

Our own summary of the model, for the `doc-quadrants` skill. It does not copy either source.

- Daniele Procida, Diátaxis: <https://diataxis.fr/>
- Steve Dunn, "Documentation quadrants":
  <https://dunnhq.com/posts/2023/documentation-quadrants/>

## The model

Documentation serves two needs on two axes. One axis is the reader's activity: *study* (the
reader is learning) or *work* (the reader is doing a task). The other is the kind of content:
*practical* (actions) or *theoretical* (knowledge). Each combination is one quadrant, and each
quadrant is a separate kind of document.

| Quadrant | Serves | Contains | Keeps out |
|---|---|---|---|
| Tutorial | Study, practical | A guided path to an outcome the author chooses | Concept explanations, options |
| How-to guide | Work, practical | Steps to solve one named problem | Basics from the tutorial |
| Reference | Work, theoretical | Complete, consistent facts about each component | Instructions, concepts |
| Explanation | Study, theoretical | Background, design reasons, how ideas connect | Instructions, component detail |

The plugin uses the name **Explanation** everywhere. Dunn calls this quadrant "Discussion".

## How to recognize each quadrant

**Tutorial.**
- Signals: "In this tutorial", "you will", one fixed example from start to end, and every step
  shows a result.
- The author chooses the goal. The reader follows and does not make choices.
- Failure sign: options or alternatives in the steps, or long asides about why the tool works.

**How-to guide.**
- Signals: a title that names a task ("How to rotate a key"), numbered steps, and the assumption
  that the reader knows the basics.
- The reader chooses the goal. The guide gives the shortest reliable path.
- Failure sign: it teaches the basics again, or it explains design.

**Reference.**
- Signals: tables, one entry per component (command, option, field, function), and the same
  structure for each entry.
- It states facts. It is complete for its scope and does not tell a story.
- Failure sign: usage steps or design discussion in the entries.

**Explanation.**
- Signals: "why", "background", "design", "trade-offs", history, and comparisons with other
  approaches.
- It connects ideas and gives reasons. A reader can read it away from the keyboard.
- Failure sign: steps to follow, or lists of options.

## Mixed sections

A section is **mixed** when it collapses two quadrants. Common mixes:

- A concept paragraph inside numbered steps (how-to + explanation).
- A full option table inside a tutorial (tutorial + reference).
- A design rationale in a reference entry (reference + explanation).
- A README "Usage" section that teaches, lists every flag, and argues for the design.

A mixed section is not always wrong. A short README can hold all four quadrants in separate
sections. The problem is two quadrants inside one section, where neither reader is served.

## Splitting a document

- Name how-to files by task: `how-to-<verb>-<object>.md`, for example `how-to-validate-input.md`.
- Name the others by quadrant and topic: `tutorial-<topic>.md`, `reference-<topic>.md`,
  `explanation-<topic>.md`, or put them in `tutorials/`, `how-to/`, `reference/` and
  `explanation/` directories.
- Keep a short landing page (often the README) that says what the project is. It routes the
  reader to each quadrant with one line per link.
- Move content whole. Do not rewrite it during the split. Rewrite in a second pass.
- Link across quadrants instead of repeating: a how-to step links to the reference entry for
  the option it uses.

## STE across the quadrants

The STE rules apply to all four quadrants. Procedural rules (imperatives, one instruction per
sentence, 20 words or fewer) dominate tutorials and how-to guides. Descriptive rules (25 words or
fewer, active voice, one topic per sentence) dominate reference and explanation.
