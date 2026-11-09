# RTK - Rust Token Killer

**Usage**: Token-optimized CLI proxy (60-90% savings on dev operations)

## Meta Commands (always use rtk directly)

```bash
rtk gain              # Show token savings analytics
rtk gain --history    # Show command usage history with savings
rtk discover          # Analyze Claude Code history for missed opportunities
rtk proxy <cmd>       # Execute raw command without filtering (for debugging)
```

## Installation Verification

```bash
rtk --version         # Should show: rtk X.Y.Z
rtk gain              # Should work (not "command not found")
which rtk             # Verify correct binary
```

⚠️ **Name collision**: If `rtk gain` fails, you may have reachingforthejack/rtk (Rust Type Kit) installed instead.

## Hook-Based Usage

A PreToolUse hook rewrites Bash commands to their rtk form (`git status` → `rtk git status`).
A rewrite happens after auto mode reviews the command, so the review no longer covers it and
the call fails with "a hook changed this call's input".

Write the rtk form yourself so the hook has nothing to change:

- `rtk git …`, `rtk ls`, `rtk grep`, `rtk diff`, `rtk find`.
- `rtk read <file> [--max-lines N]`, not `cat` or `head`.
- When unsure of the form, check it with `rtk hook check '<cmd>'`.
- Prefer the Read, Grep and Glob tools to shell reads. They bypass Bash, the hook and the
  classifier.
- Keep each Bash call to one command or a short chain. A long `;` chain gets several
  rewrites, and a failed call costs more to retry.

Refer to CLAUDE.md for full command reference.
