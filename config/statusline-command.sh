#!/usr/bin/env bash
# Claude Code status line — mirrors ~/.bashrc PS1: user@host:path
# with additional Claude session info appended.

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

printf "%s %s\n" "$ps1_part" "$claude_part"
