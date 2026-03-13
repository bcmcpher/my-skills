# MCP Server Configuration Reference

MCP (Model Context Protocol) servers extend Claude with tools that reach outside the
local filesystem — web search, data versioning, API integrations, and more. Configure
servers in `.mcp.json` at the project root (project-local) or `~/.claude/.mcp.json`
(global, available in all sessions).

---

## .mcp.json format

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "<executable>",
      "args": ["<arg1>", "<arg2>"],
      "env": {
        "API_KEY": "<your-key>"
      }
    }
  }
}
```

Multiple servers can be defined in the same file. Each runs as a subprocess managed
by Claude Code.

---

## DataLad (datalad-cli plugin)

**Applicability:** data-analysis (strongly recommended), info-management (recommended
for binary-heavy collections), coding-tool (optional).

DataLad is not an MCP server — it is a Claude Code plugin that provides skills
(slash commands and auto-invoked behaviors) for data versioning and provenance
tracking. It integrates with `git-annex` under the hood.

**Install:**
```bash
claude plugin install <path-to-datalad-cli>
# or from the my-skills repo:
claude plugin install ./plugins/datalad-cli
```

**What it enables:**

| Skill | When Claude uses it |
|---|---|
| `datalad-init` | Initialize a new dataset |
| `datalad-save` | Record changes to tracked files |
| `datalad-run` | Run a command with provenance recording |
| `datalad-get` | Retrieve annexed files on demand |
| `datalad-push` | Push data to a remote |
| `datalad-addurls` | Register files from URLs |
| `datalad-clone` | Clone a remote dataset |
| `datalad-status` | Check dataset status |

**When to recommend it:**

- Any project where raw data is too large to commit to git directly
- Projects with binary outputs (PDFs, models, figures) needing provenance
- Info-management collections that include PDFs, EPUBs, or exported documents
- Any project where collaborators need to selectively `get` files

**System requirement:** `git-annex` must be installed separately:
```bash
# Debian/Ubuntu
sudo apt install git-annex

# macOS
brew install git-annex

# Conda
conda install -c conda-forge git-annex
```

---

## Web Search

**Applicability:** info-management (strongly recommended), data-analysis (useful for
literature search), coding-tool (optional).

Several MCP-compatible web search servers are available. Choose based on access and
preference:

### Brave Search MCP

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": {
        "BRAVE_API_KEY": "<your-brave-api-key>"
      }
    }
  }
}
```

Get a key at: https://api.search.brave.com/

### Tavily MCP

```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp"],
      "env": {
        "TAVILY_API_KEY": "<your-tavily-api-key>"
      }
    }
  }
}
```

Get a key at: https://tavily.com/

### Exa MCP

```json
{
  "mcpServers": {
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp-server"],
      "env": {
        "EXA_API_KEY": "<your-exa-api-key>"
      }
    }
  }
}
```

Get a key at: https://exa.ai/

---

## GitHub MCP

**Applicability:** coding-tool (recommended for hosted projects), data-analysis
(optional, for analysis repos on GitHub).

The GitHub MCP server enables Claude to read and interact with GitHub repositories,
issues, and pull requests within a session.

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-pat>"
      }
    }
  }
}
```

Create a PAT at: GitHub → Settings → Developer settings → Personal access tokens.
Required scopes: `repo`, `read:org` (for org repos).

**What it enables:** reading PRs and issues, posting comments, checking CI status,
listing repository files — all without leaving Claude Code.

---

## Filesystem MCP

**Applicability:** info-management (useful for large collections), any project with
files outside the current working directory.

The filesystem MCP server lets Claude access files in specified directories beyond
the current project root.

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/path/to/allowed/dir1",
        "/path/to/allowed/dir2"
      ]
    }
  }
}
```

Only the directories listed as args are accessible. Do not include sensitive directories.

---

## Recommendations by project type

| Project type | Priority MCPs |
|---|---|
| `coding-tool` | GitHub MCP |
| `data-analysis` | DataLad (plugin), GitHub MCP |
| `info-management` | Web search MCP, DataLad (plugin), Filesystem MCP (optional) |

---

## Security notes

- Store API keys in environment variables or a secrets manager — never hardcode them
  in `.mcp.json` if the file will be committed.
- Add `.mcp.json` to `.gitignore` if it contains tokens, or use a separate
  `.mcp.local.json` for secrets and commit only the structure.
- MCP servers run as subprocesses with access to the network and file system. Only
  install servers from trusted sources.
