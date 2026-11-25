#!/bin/bash
# rtk-rewrite.sh — PreToolUse hook for Bash: run `rtk hook claude`, except in auto mode.
#
# In auto mode the server-side classifier reviews the command the model wrote. A hook
# that returns `updatedInput` changes the command after that review, so Claude Code
# refuses it ("a hook changed this call's input after auto mode reviewed it"), or sends
# it to a slower local classifier. rtk's rewrite (grep -> rtk grep, ls -> rtk ls) is
# exactly such a change. Upstream: rtk-ai/rtk#4627, anthropics/claude-code#102469.
#
# So in auto mode this hook does nothing, and the model types the `rtk` prefix itself
# (RTK.md says to), which the server then reviews as written. Every other mode gets
# the normal rewrite.
#
# Remove this wrapper, and call `rtk hook claude` directly again, once rtk can skip
# auto mode itself or Claude Code reviews hook-rewritten input.

input=$(cat)

mode=$(jq -r '.permission_mode // empty' <<<"$input" 2>/dev/null)
if [[ "$mode" == "auto" ]]; then
    exit 0
fi

exec rtk hook claude <<<"$input"
