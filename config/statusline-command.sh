#!/usr/bin/env bash
# Claude Code status line — mirrors ~/.bashrc PS1: user@host:path
# with Claude session info and the caveman mode badge appended.

input=$(cat)

cwd=$(echo "$input" | jq -r '.workspace.current_dir // .cwd')
model=$(echo "$input" | jq -r '.model.display_name // ""')
remaining=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')

# PS1-style prefix: \033[01;32m = bold green, \033[01;34m = bold blue, \033[00m = reset
ps1_part=$(printf "\033[01;32m%s@%s\033[00m:\033[01;34m%s\033[00m" \
    "$(whoami)" "$(hostname -s)" "$cwd")

# Claude session info
claude_part="[$model"
if [ -n "$remaining" ]; then
    claude_part="$claude_part | ctx: ${remaining}% left"
fi
claude_part="$claude_part]"

# caveman mode badge. Delegated to the plugin's own script rather than
# reimplemented: it reads session_id from the same stdin JSON and reports THIS
# window's mode (the legacy ~/.claude/.caveman-active mirror is last-write-wins
# across windows), and it renders nothing when the mode is off rather than a
# misleading [CAVEMAN:OFF]. Guarded so the status line still works without caveman.
caveman_part=""
caveman_sl="$HOME/.claude/plugins/marketplaces/caveman/src/hooks/caveman-statusline.sh"
if [ -r "$caveman_sl" ]; then
    caveman_part=$(printf '%s' "$input" | bash "$caveman_sl" 2>/dev/null)
fi

printf "%s %s%s\n" "$ps1_part" "$claude_part" "${caveman_part:+ $caveman_part}"
