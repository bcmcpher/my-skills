---
name: datalad-siblings
description: >
  Auto-invoke when the user wants to inspect, add, configure, or remove dataset remotes;
  set up a GitHub, OSF, S3, or other storage sibling; check what remotes exist; or
  configure where to push annexed data. Trigger on "list remotes", "add a remote",
  "configure sibling", "set up GitHub", "add OSF storage", "what siblings exist",
  "where is this data stored", or /datalad-siblings. Do NOT trigger for plain git
  remote operations outside a DataLad dataset.
argument-hint: [query|add|configure|remove|enable] [-s name] [--url url]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Bash, Glob
---

# Skill: datalad-siblings

Inspect and configure sibling remotes — named locations where dataset history and/or
annexed file content can be pushed and pulled.

## Steps

1. **Verify DataLad context** — check for `.datalad/` in the current directory or a
   parent:
   ```bash
   ls .datalad/ 2>/dev/null
   ```
   If no dataset is found, inform the user and stop.

2. **Determine action** — read from `$ARGUMENTS` or conversation context:
   - **query** (default, no subcommand): list all configured siblings
   - **add**: register a new sibling
   - **configure**: change a property of an existing sibling
   - **remove**: unregister a sibling
   - **enable**: activate a special remote (e.g., S3, OSF) after cloning

3. **Execute based on action**:

   ### query
   ```bash
   datalad siblings
   ```
   Present the output. Explain the `+`/`-` indicator and sibling types.

   ### add
   Gather from the user:
   - Sibling name (e.g., `github`, `osf-storage`, `backup`)
   - URL (fetch URL — see reference for format options)
   - Whether a separate `--pushurl` is needed (common when fetch is HTTPS but push
     requires SSH):
     > "Do you need a separate push URL (e.g., SSH for write access)?"
   - Whether a `--publish-depends` should be set — ask if a storage sibling already
     exists or is being added alongside a git host:
     > "Should pushing to this sibling automatically push annexed content to a storage
     > sibling first? If so, which storage sibling?"

   Construct:
   ```
   datalad siblings add -s <name> \
       --url <url> \
       [--pushurl <push-url>] \
       [--publish-depends <storage-sibling>]
   ```

   ### configure
   Gather which sibling and which property to change. Common properties:
   - `--url` / `--pushurl`
   - `--annex-wanted` / `--annex-required`
   - `--publish-depends`

   ```
   datalad siblings configure -s <name> [--annex-wanted '<expression>']
   ```

   ### remove
   Confirm the sibling name. Warn that this only removes the registration — it does
   not delete remote content.
   ```
   datalad siblings remove -s <name>
   ```

   ### enable
   Used after cloning a dataset whose special remote (OSF, S3, WebDAV) needs activation:
   ```
   datalad siblings enable -s <name>
   ```

4. **Show command and execute** — always display the full command before running.

5. **Post-add suggestion** — after adding or configuring a sibling, suggest:
   > "Run `datalad push --to <name>` to test connectivity and push your current state."

## Reference

Always load `${CLAUDE_PLUGIN_ROOT}/../references/siblings-and-remotes.md` for URL
formats, special remote types, publish-depends patterns, and annex-wanted expressions.

## Constraints

- Never conflate a **sibling** (DataLad concept, wraps git remote + annex) with a raw
  `git remote` — direct `git remote add` bypasses annex configuration.
- Never skip the `--publish-depends` question when a storage sibling exists alongside a
  git host — failing to set it causes `datalad push` to push git history without annexed
  content, breaking reproducibility for downstream consumers.
- Always show the full command before executing.
- For `remove`, always confirm the sibling name before proceeding — it cannot be undone
  without re-adding.
