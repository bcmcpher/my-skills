# Post-restart verification

Point a fresh session at this file after changing global config. Expected results are inline —
anything else is a regression.

## Outstanding

- [ ] **Rotate `OPENAI_API_KEY`.** `zotero-cli config` prints it unmasked and it was exposed in a
      transcript on 2026-09-02. Not automatable; clear this box once done.

## Automated — run this block

```bash
cd ~/Projects/claude/my-skills
bin/test-hooks         && echo OK   # want: OK, and no FAIL lines
bin/test-hooks --repo  && echo OK   # want: OK, and no FAIL lines
bin/rebuild-tools --check           # want: All good.

# rm moved deny -> ask
jq -r '[.permissions.deny[]|select(test("rm"))]|length' ~/.claude/settings.json   # want: 0
jq -r '[.permissions.ask[]|select(test("rm "))]|length' ~/.claude/settings.json   # want: 2 (rm, rtk rm)

# zotero: read-only env set, `config` NOT allow-listed (it leaks OPENAI_API_KEY)
jq -r '.env.ZOTERO_LOCAL' ~/.claude/settings.json                                # want: true
jq -r '[.permissions.allow[]|select(test("zotero-cli config"))]|length' ~/.claude/settings.json  # want: 0

# Zotero desktop running with Settings > Advanced > local API enabled
curl -s -o /dev/null -w '%{http_code}\n' --max-time 4 \
  'http://localhost:23119/api/users/0/items?limit=1'                             # want: 200

ls ~/.claude/skills/                # want: youtube-transcript/ and zotero-cli/ present

# opencite: query verbs allow-listed, retrieval and config verbs are NOT
jq -r '[.permissions.allow[]|select(test("opencite"))]|length' ~/.claude/settings.json           # want: 5
jq -r '[.permissions.allow[]|select(test("opencite (pdf|convert|batch-fetch|config)"))]|length' \
  ~/.claude/settings.json                                                                        # want: 0
jq -r '.enabledPlugins["opencite@research-skills"]' ~/.claude/settings.json                      # want: true

# opencite resolves the way a skill's Bash call sees it, and has the [pdf] extra
env -i PATH="$HOME/.claude-lsp-tools/bin:/usr/bin:/bin" HOME="$HOME" \
  bash -c 'opencite --version'                                                  # want: opencite 0.5.4+
~/.claude-lsp-tools/bin/python -c 'import markitdown, markit_mistral'           # want: silence
```

## Manual — needs a live session

| Check | Expected |
|---|---|
| `rm -rf ./some-scratch-dir` | **prompts** (used to be a hard deny) |
| `rm -rf ~` | **blocked** by bash-guard, names the target |
| `rm -rf /tmp/foo` | **prompts, not blocked** — the false-positive case that matters most |
| Paste a YouTube link, ask for a summary | `youtube-transcript` fires; prompts once for `yt-dlp` |
| Ask about a paper in your library | `zotero-cli` runs **unprompted** (read subcommands are allow-listed) |
| `claude mcp list` | **no** zotero server — it is a CLI skill on purpose, see `README.md` |
| Ask to find papers on a topic | `opencite` skill fires; `opencite search` runs **unprompted** |
| Ask it to download a paper's PDF | `opencite pdf` **prompts** — retrieval is not allow-listed |
| Watch the command it writes | bare `opencite`, **not** `uvx opencite` (see `CLAUDE.md`) |

## If something fails

- Hook cases fail → `config/hooks/bash-guard.sh` and `~/.claude/hooks/bash-guard.sh` have drifted;
  `cp` the repo copy over the live one and re-run.
- `rebuild-tools --check` reports a missing package → `bin/rebuild-tools`, then `--freeze` only if
  the resulting lock diff is one you meant.
- Zotero returns `Local API is not enabled` → the toggle is off; the connector port answering 200
  is not the same thing.
- **Do not run `bin/sync-config push` to repair a single item** — it reverts live-only plugin and
  marketplace state. Hand-apply instead; see "Sync workflow" in `README.md`.
