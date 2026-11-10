# Obsidian vault as the memory backend

Status: research, created 2026-03-19, moved here from memory 2026-11-09. Blocked on an
evaluation of the available Obsidian MCP servers. The design below dates from 2026-03 and has
not been checked against the current Claude Code memory system.

## Goal

Replace the flat-file memory (`~/.claude/projects/*/memory/`) with an Obsidian vault. Plans,
session notes and research can then be linked, shown as a graph, and edited outside Claude.
Edits to vault notes become context in later sessions.

## Next step: evaluate the MCP servers

Evaluate these before refining the plan or building a server:

- `mcp-obsidian` (GitHub search);
- `obsidian-mcp` (GitHub search);
- any server that wraps the Local REST API plugin (`obsidian-local-rest-api`).

Questions for each:

1. Does it work offline on the files, or does it need Obsidian running (REST API)?
2. Does it give backlinks?
3. Does it give full-text search?
4. Can it create and write notes?
5. How good is it, and is it maintained?

The repo's rule applies: when a capability ships both an MCP server and a CLI, take the CLI and
put a skill around it (see the repo `CLAUDE.md`).

## Architecture (draft, 2026-03)

### Obsidian interfaces

| Interface | Needs Obsidian running? | Notes |
|---|---|---|
| File system (direct read and write) | No | Always available; parse `[[links]]` by hand |
| Local REST API plugin | Yes | Richer API; community plugin `obsidian-local-rest-api` |
| Dataview plugin | Yes (renderer) | SQL-like queries; not usable from outside processes |

### Layers

1. **Vault as the memory backend.** Move the memory directory into a vault subfolder,
   `vault/claude/memory/`, and update the memory path reference. No new infrastructure, and
   Obsidian indexes it at once. Limit: no link traversal.
2. **Server with graph traversal.** Tools: `vault_search(query)`, `vault_read(path)`,
   `vault_write(path, content)`, `vault_backlinks(path)`, `vault_forward_links(path)`,
   `vault_query_tag(tag)`. Adopt a community server or build one (FastMCP in Python, or the
   MCP TypeScript SDK). Prefer the file-system approach: it does not depend on Obsidian.
3. **Note conventions.** Frontmatter per note type:

   ```yaml
   # sessions/YYYY-MM-DD-<topic>.md
   ---
   type: session
   date: YYYY-MM-DD
   project: <project>
   tags: [...]
   status: complete | in-progress
   linked-plans: [[plans/<plan-name>]]
   ---
   ```

   ```yaml
   # plans/<name>.md
   ---
   type: plan
   status: draft | in-progress | complete
   created: YYYY-MM-DD
   tags: [...]
   ---
   ```

4. **Context at session start.** Static: `CLAUDE.md` `@`-imports for notes that always load,
   such as an index of active plans. Dynamic: a tool call at session start that searches notes
   by project or tag.

### Vault layout

```
vault/
└── claude/
    ├── memory/
    │   ├── MEMORY.md          # index (existing format)
    │   └── *.md               # existing memory files
    ├── sessions/              # per-conversation notes
    └── plans/                 # design and implementation plans
```

## Build order

| Step | What | Effort |
|---|---|---|
| 1 | Move the memory directory into the vault; update the path | 10 min |
| 2 | Define the frontmatter for each note type | 30 min |
| 3 | Adopt or build a file-system server (search and link traversal) | 2–4 h |
| 4 | Add session and plan note templates | 30 min |
| 5 | Add `@`-imports for active plans to `CLAUDE.md` | 10 min |

Step 1 gives value at once, with no risk. Steps 3–5 add graph traversal and dynamic context.

## Open before step 1

- Does the current memory system still allow its directory to move? The 2026-03 draft assumed
  a path reference in `CLAUDE.md`. Check this first.
- How do vault plans relate to this repo's `plans/`? Two plan locations would conflict.
