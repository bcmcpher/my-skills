# Project Type: Information Management

## Description

A structured knowledge collection — somewhere between an executive assistant and a
research aggregator. Claude's role is to help capture, organize, synthesize, and
surface information rather than write code. The primary value is in the MCP and agent
integrations that facilitate research aggregation, not in a programming environment.

## Primary language

None. This project has no programming environment. Git (or DataLad for binary-heavy
collections) is used for version control of the knowledge base itself.

---

## Directory scaffold

```
<name>/
├── inbox/                # unsorted captures — processed regularly
├── notes/
│   ├── areas/            # ongoing responsibilities, long-running topics
│   └── resources/        # reference material with long-term value
├── research/             # structured investigation outputs
├── outputs/              # polished deliverables: memos, briefings, summaries
├── archive/              # completed, superseded, or inactive items
├── .gitignore
└── README.md             # scope statement, filing conventions, tagging taxonomy
```

**Alternative structures** — choose what fits your mental model:

| Model | Top-level dirs |
|---|---|
| PARA (default above) | `inbox/`, `notes/areas/`, `notes/resources/`, `research/`, `outputs/`, `archive/` |
| Chronological | `YYYY/`, `YYYY-MM/` — everything dated, browsed by time |
| Topic-based | One dir per subject area; flat within each |
| Zettelkasten | `notes/` (atomic, densely linked); `index.md` as entry point |
| Project-based | One dir per active initiative; `archive/` when done |

Ask the user which model to use, or default to PARA.

---

## Essential files

### README.md

This file is the human-readable companion to CLAUDE.md. It documents the collection
for collaborators (or future self) without relying on Claude to explain it.

```markdown
# <name>

<description>

## Scope

**In scope:** <what belongs here>
**Out of scope:** <what doesn't belong here>

## Filing conventions

<describe your filing model and note-naming convention>

Example: Notes follow `YYYY-MM-DD-slug.md`. Items in `inbox/` are unsorted and
reviewed regularly. Completed research outputs go to `outputs/`; raw research notes
go to `research/`.

## Tagging

| Tag | Meaning |
|---|---|
| `#inbox` | Unsorted, needs filing |
| `#active` | Currently relevant |
| `#archived` | No longer active |
| `#pending-review` | Awaiting action |
| ... | ... |

## Tools

- Version control: <git / DataLad>
- Note format: <Markdown / Obsidian / plain text>
- Sync: <if applicable>
```

---

## .gitignore additions

```
# OS artifacts
.DS_Store
Thumbs.db
desktop.ini

# Editor temp files
*.swp
*.swo
*~
.obsidian/workspace.json

# Large binaries — track with DataLad instead
# (remove these lines if files are small enough to commit directly)
*.pdf
*.epub
*.docx
*.mp4
*.mp3
```

---

## DataLad consideration

DataLad is preferred over plain git for information management collections that include
binary files (PDFs, EPUBs, exported documents, audio/video). Key advantages:

- Binary files are stored in an annex; git history stays lightweight
- Remote sources (URLs, DOIs) can be registered so files are retrievable on demand
- `datalad get <file>` fetches a binary without downloading the entire collection
- `datalad drop <file>` frees local disk space while preserving the reference

If the `datalad-cli` plugin is installed, Claude can use DataLad skills throughout
this project. Recommend initializing as a DataLad dataset if binary files are expected:

```bash
datalad create <name>
cd <name>

# Register a PDF from a URL
datalad download-url https://example.com/paper.pdf --path research/paper.pdf -m "Add paper"

# Or register many files from a list
datalad addurls urls.csv --path inbox/{filename}
```

The `datalad-cli` plugin provides skills for `datalad-init`, `datalad-save`,
`datalad-get`, `datalad-push`, `datalad-addurls`, and others.

---

## CLAUDE.md template

The CLAUDE.md for an information management project is the most important configuration
artifact — it defines Claude's operating context, filing logic, and behavioral
constraints. The template below includes commented options to help you tailor it.

```markdown
## Project

**Type:** info-management
**Description:** <one-sentence description of what this collection covers>

## Collection scope

<!-- Be specific. Claude uses this to decide whether new material belongs here
     and to avoid retrieving irrelevant content when you ask questions. -->

**In scope:**
- <topic, source type, or domain 1>
- <topic, source type, or domain 2>
- <topic, source type, or domain 3>

**Out of scope:**
- <what explicitly does not belong here>

**Primary audience:** <self | team | leadership | public>

## Input types

<!-- Check all that apply. These tell Claude what to expect in inbox/ and how
     to handle different file types. -->

- [ ] Web articles / blog posts
- [ ] Academic papers / preprints (PDF)
- [ ] Books or book chapters
- [ ] Meeting notes or transcripts
- [ ] Email threads or newsletter exports
- [ ] Slack / chat exports
- [ ] Internal documents or slide decks
- [ ] Interview or conversation notes
- [ ] Personal observations and annotations
- [ ] Data tables or spreadsheets

## Output types

<!-- What should Claude produce from this collection? -->

- [ ] Executive summaries (1-page, bullet-point)
- [ ] Literature reviews and synthesis notes
- [ ] Weekly or monthly briefings
- [ ] Action item lists
- [ ] Research memos
- [ ] Slide outlines
- [ ] Structured tables or comparisons
- [ ] Draft reports or white papers

## Filing conventions

**Model:** PARA  <!-- or: Chronological / Topic-based / Zettelkasten / Project-based -->
**Note naming:** `YYYY-MM-DD-slug.md`  <!-- or: freeform / topic-prefixed / numbered -->
**Inbox policy:** <review daily / weekly / on demand>

<!-- Describe any other filing rules Claude should follow: -->
<additional conventions>

## Tagging taxonomy

<!-- Consistent tags help Claude surface related material across directories.
     Define your vocabulary here; Claude will use only these tags. -->

**Status:** `#inbox` `#active` `#archived` `#pending-review`
**Type:** `#article` `#paper` `#meeting` `#memo` `#data` `#book`
**Topic:** <add your domain-specific tags>

## How Claude should help

<!-- Be explicit. The examples below are common patterns — keep what fits,
     remove what doesn't, and add project-specific behaviors. -->

**When I drop a file in `inbox/`:**
Summarize it in 3–5 bullets. Suggest a tag set and a filing location in `notes/`.
Ask before filing — don't move files automatically.

**When I ask "what do we know about X?":**
Search `notes/` and `research/` for relevant material. Produce a synthesis note
citing specific files. Do not fabricate content not present in the collection.

**When I ask for a briefing:**
Scan `inbox/` for recent items (past 7 days by default). Produce a structured
summary grouped by topic or type. List items that need action separately.

**When I ask Claude to research X:**
Use available web search tools to gather current information. Synthesize findings
into a structured note. Save output to `research/<YYYY-MM-DD-slug>.md`. Cite sources.

**When I ask Claude to produce an output:**
Draw from `notes/` and `research/` for content. Draft in `outputs/<slug>.md`.
List the sources used at the bottom of the draft.

**When I ask Claude to process inbox:**
List all items in `inbox/`. For each, show: summary, suggested tags, suggested
filing location. Wait for my approval before moving anything.

## Research and aggregation tools

<!-- List tools Claude can use to gather and manage information. -->

- Web search: <MCP server name, or "not configured — install a web search MCP">
- DataLad: <"available via datalad-cli plugin" or "not configured">
- <other integrations: calendar, email, RSS, Zotero, etc.>

## Constraints

<!-- Explicit constraints prevent well-intentioned but unwanted behavior.
     Customize this list for your workflow. -->

- Do not delete or move files without showing the proposed change and waiting for
  confirmation.
- Do not summarize a document without noting the source file path.
- Do not file inbox items automatically — always surface the decision first.
- Do not add content to `notes/` or `research/` without the user's explicit request.
- When uncertain whether material fits the collection scope, ask rather than assume.
- <add project-specific constraints>
```

---

## Recommended Claude configuration

### LSP

Not applicable for information management projects.

### Hooks

Not applicable. (Optionally, a markdown formatter like `prettier --write $FILE` can
be added as a PostToolUse hook if consistent Markdown style is important.)

### MCP

**High value** — MCP integrations are the primary differentiator for this project type.

- **Web search MCP**: for research aggregation tasks. Recommended: Brave Search MCP,
  Tavily, or Exa. Without web search, Claude can only work with files already in the
  collection.
- **DataLad** (`datalad-cli` plugin): for binary file management (PDFs, EPUBs, exports).
  Strongly recommended if the collection will include non-text files.
- **Additional options** (project-specific):
  - Calendar / email MCP: for meeting notes and inbox processing workflows
  - Zotero MCP: for academic reference management
  - RSS / feed reader MCP: for monitoring sources automatically

See `references/claude-config/mcp.md` for configuration snippets.

### Recommended agents

**researcher**

```yaml
name: researcher
description: >
  Given a question or topic, searches available sources (web search MCP if configured,
  plus the local collection), synthesizes findings, and saves a structured research
  note to research/. Aware of DataLad for managing retrieved binary files. Use when
  asked to "research X", "find out about Y", or "pull together what we know on Z".
tools: Read, Grep, Glob, Write, Bash
model: inherit
permissionMode: default
maxTurns: 25
```

Body: Accept a research question from the user. Search the local collection first
(`notes/`, `research/`). If web search MCP is available, supplement with current
sources. Synthesize into a structured note with sections: Summary, Key findings,
Open questions, Sources. Save to `research/YYYY-MM-DD-<slug>.md`.

If retrieved sources include binary files (PDFs, etc.) and DataLad is initialized,
use `datalad download-url` or `datalad addurls` to register them in the collection
rather than saving loose copies. DataLad tools are available via the `datalad-cli`
plugin if installed.

---

**summarizer**

```yaml
name: summarizer
description: >
  Condenses a document, thread, or set of notes into a structured summary note.
  Use when asked to "summarize this", "distill these notes", or "what are the
  key points of X".
tools: Read, Glob, Write
model: inherit
permissionMode: default
maxTurns: 10
```

Body: Read the target file(s). Produce a summary with: one-paragraph abstract,
bullet-point key points, and any action items or open questions. Save to
`notes/resources/YYYY-MM-DD-summary-<slug>.md`. Cite the source file path.
Do not include information not present in the source material.

---

**inbox-processor**

```yaml
name: inbox-processor
description: >
  Reviews all files in inbox/, summarizes each, and proposes filing decisions
  (tags + destination directory). Never moves files without explicit user approval.
  Use when asked to "process the inbox", "triage inbox", or "what's in my inbox".
tools: Read, Glob, Bash
model: inherit
permissionMode: default
maxTurns: 20
```

Body: List all files in `inbox/`. For each file: read it, produce a 2–3 sentence
summary, suggest a tag set from the collection's tagging taxonomy (in CLAUDE.md),
and propose a filing location. Present all proposals together and wait for the user
to approve, modify, or reject each one. Do not move or rename any file until
explicitly approved. After approval, report what was moved.

If binary files are in `inbox/` and DataLad is initialized, suggest registering
them with `datalad save` rather than leaving them as untracked files. DataLad tools
are available via the `datalad-cli` plugin if installed.

---

**briefing-writer**

```yaml
name: briefing-writer
description: >
  Scans recent inbox items and active notes to produce a structured briefing
  document. Use when asked for a "weekly briefing", "status update", "what happened
  this week", or "morning brief".
tools: Read, Grep, Glob, Write, Bash
model: inherit
permissionMode: default
maxTurns: 15
```

Body: Determine the time window (default: past 7 days; adjust based on user request).
Scan `inbox/` and `notes/areas/` for recently modified files. Produce a structured
briefing: Highlights (top 3–5 items), By topic/area, Action items, Items pending
review. Save to `outputs/YYYY-MM-DD-briefing.md`. Do not fabricate content — only
report what is present in the collection.

### Recommended local skills

**`/file-note`** — prompts for a title and content, creates a dated note in the
appropriate `notes/` subdirectory based on a type tag.

**`/research`** — shorthand for invoking the `researcher` agent with a given topic.
