# Stop tracking openspec's per-machine anonymousId

Status: draft, 2026-11-09. Not started. The open decision is settled (see "openspec's behaviour
with no ID"); awaiting go-ahead.

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
2. **`push`:** no change. It copies the ID-less file, which is safe (see below).
3. **Repo copy:** remove `anonymousId` from `config/xdg/openspec/config.json`. Keep `noticeSeen`
   and `enabled: false`.
4. **Comment:** at `XDG_TRACKED`, note that per-install fields are stripped on `pull`, and name
   them.

### openspec's behaviour with no ID (checked 2026-11-09)

openspec 1.11.0 ran in a throwaway `HOME` and `XDG_CONFIG_HOME`, with a config that had
`enabled: false` and no `anonymousId`. `--version`, `config list` and `init --tools none` all
exited 0. None of them changed the file: no ID was created, and `enabled` stayed false. With
telemetry off, openspec does not need the ID at all.

So `push` needs no merge step. A push removes a machine's existing ID, which matters only if
telemetry is turned back on there. A merge step to keep it was considered and dropped as
unneeded.

## Verification

- `bin/sync-config pull` leaves `config/xdg/openspec/config.json` with no `anonymousId`, and a
  second `pull` shows no diff for that file.
- `bin/sync-config push` on this machine is NOT used for the test: it also overwrites the live
  `settings.json`. Test only with a throwaway `HOME`.
- shellcheck clean.

## Out of scope

- Rewriting history to remove the old ID.
- A general mechanism for per-machine fields in other tracked files. Two cases do not justify
  one yet.
