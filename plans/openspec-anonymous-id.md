# Stop tracking openspec's per-machine anonymousId

Status: draft, 2026-11-09. Not started. One open decision below.

## Context

`bin/sync-config` mirrors `~/.config/openspec/config.json` into `config/xdg/openspec/config.json`.
It does this so a new machine keeps `telemetry.enabled: false`, because openspec turns telemetry
back on by default. The file also holds `telemetry.anonymousId`, a UUID that identifies one
install. That has two effects:

- `pull` writes this machine's ID into the repo. The tracked ID already differs from the live
  one, so every `pull` shows a diff with no meaning.
- `push` copies one machine's ID to every other machine. If telemetry is ever re-enabled, every
  machine then reports as the same install.

`sync-config` already strips one machine-specific field on `pull`:
`extraKnownMarketplaces.local` in `settings.json` (lines 51–62). The fix follows that pattern.

The ID is low-sensitivity: telemetry is disabled, and the value identifies an install, not a
person. Rewriting git history to remove the old value is not worth the cost.

## Changes

1. **`pull`:** after copying `openspec/config.json`, delete `.telemetry.anonymousId` with jq,
   the same way the marketplace path is stripped. Print `strip telemetry.anonymousId
   (per-install)`.
2. **`push`:** do not overwrite a live ID. If the live file has `.telemetry.anonymousId`,
   merge it back into the copied file with jq. If the live file is absent, copy the tracked file
   as it is.
3. **Repo copy:** remove `anonymousId` from `config/xdg/openspec/config.json`. Keep `noticeSeen`
   and `enabled: false`.
4. **Comment:** at `XDG_TRACKED`, note that per-install fields are stripped on `pull`, and name
   them.

**Open decision: what openspec does when the ID is missing.** Before step 2, check
openspec's behaviour with a throwaway home:
`env HOME="$(mktemp -d)" XDG_CONFIG_HOME="$HOME/.config" ~/.claude-node-tools/bin/openspec --version`,
with a config file that has no `anonymousId`.

- If openspec creates a new ID and keeps `enabled: false`, the push-side merge in step 2 is
  enough. **Recommended, if confirmed.**
- If openspec rewrites the file and resets `enabled` to true, `push` must also re-assert
  `enabled: false` after the merge. Record that in the comment.

## Verification

- `bin/sync-config pull` leaves `config/xdg/openspec/config.json` with no `anonymousId`, and a
  second `pull` shows no diff for that file.
- In a throwaway `HOME`/`XDG_CONFIG_HOME` that already holds a config with an ID, `push` keeps
  that ID. With no live file, `push` copies the tracked file.
- `bin/sync-config push` on this machine is NOT used for the test: it also overwrites the live
  `settings.json`. Test only with a throwaway `HOME`.
- shellcheck clean.

## Out of scope

- Rewriting history to remove the old ID.
- A general mechanism for per-machine fields in other tracked files. Two cases do not justify
  one yet.
