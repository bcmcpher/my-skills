#!/bin/bash
# protect-files.sh — PreToolUse hook for Write, Edit, MultiEdit and NotebookEdit.
#
# Blocks edits to secrets, the lock file and git internals. It matches PATH
# COMPONENTS, not substrings: `.env.example` and `.github/` are ordinary files,
# while `.env.local`, `key.pem` and anything under a `.git` directory are not.
# NotebookEdit sends `notebook_path` rather than `file_path`, so both are read.
#
# This hook never evaluates its input; it only compares the path with `case`.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -z "$FILE_PATH" ] && exit 0

block() { echo "Blocked: $FILE_PATH $1" >&2; exit 2; }

case "${FILE_PATH##*/}" in
  .env.example|.env.sample|.env.template) ;;
  .env|.env.*)       block "is an environment file that may hold secrets" ;;
  *.pem|*.key)       block "is a key or certificate file" ;;
  package-lock.json) block "is a generated lock file" ;;
esac

case "/$FILE_PATH/" in
  */.git/*) block "is inside a .git directory" ;;
esac

case "$FILE_PATH" in
  "$HOME"/.ssh/*|"$HOME"/.aws/*|"$HOME"/.gnupg/*) block "is inside a credential directory" ;;
esac

exit 0
