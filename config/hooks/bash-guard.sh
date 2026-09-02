#!/bin/bash
# bash-guard.sh — PreToolUse hook for Bash.
#
# Covers four classes of command that the permission glob syntax cannot express,
# so that Bash(find *), Bash(echo *) and Bash(gh api:*) can stay in `allow`
# without their sharp edges.
#
# Every rule matches an ARGUMENT POSITION, never raw command text. The deleted
# git-guard.sh matched ".git/" anywhere in the command and so blocked the
# ordinary idiom `find . -not -path "./.git/*"`. Rules here are anchored to a
# command word or a flag, and each has a negative test in the matrix.
#
# rtk rewrites commands before this runs in some orderings (git -> rtk git,
# cat -> rtk read), so every command matcher accepts an optional "rtk " prefix.

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# Strip heredoc bodies before matching. Their content is DATA, not commands: a
# commit message describing `gh api` rules, or a doc listing `echo x >> ~/.bashrc`
# as an example, is not an invocation. Without this the rules below fire on
# prose, which is both wrong and very confusing when it happens.
CMD=$(printf '%s\n' "$CMD" | awk '
  inhd { if ($0 == marker || $0 == marker";") inhd=0; next }
  {
    line=$0
    if (match(line, /<<-?[ \t]*['"'"'"]?[A-Za-z_][A-Za-z0-9_]*['"'"'"]?/)) {
      m=substr(line, RSTART, RLENGTH)
      sub(/^<<-?[ \t]*/, "", m)
      gsub(/['"'"'"]/, "", m)
      marker=m; inhd=1
    }
    print line
  }
')
[ -z "$CMD" ] && exit 0

block() { echo "Blocked: $1" >&2; exit 2; }

# Command word: start of string, or after a pipe/semicolon/&&/newline.
CW='(^|[|;&]|[[:space:]])'

# ---------------------------------------------------------------- 1. find
# -delete and -exec/-execdir/-ok/-okdir turn an allow-listed read command into
# an arbitrary-deletion primitive.
if printf '%s' "$CMD" | grep -qE "${CW}(rtk[[:space:]]+)?find([[:space:]]|\$)"; then
  if printf '%s' "$CMD" | grep -qE '[[:space:]]-(delete|exec|execdir|ok|okdir)([[:space:]]|$)'; then
    block "find with -delete/-exec is destructive; Bash(find *) only covers searching"
  fi
fi

# ------------------------------------------------------- 2. redirection targets
# Writing via `>` bypasses both Write/Edit sitting in `ask` and the
# protect-files.sh hook. Only sensitive destinations are blocked -- redirecting
# into the worktree or /tmp is ordinary work and stays allowed.
TARGETS=$(printf '%s' "$CMD" | grep -oE '>>?[[:space:]]*[^[:space:];&|<>)]+' | sed -E 's/^>>?[[:space:]]*//')
for t in $TARGETS; do
  case "$t" in
    /dev/null|/dev/stdout|/dev/stderr|'&1'|'&2') continue ;;
  esac
  case "$t" in "~"*) t="${HOME}${t#\~}" ;; esac
  case "$t" in
    "$HOME"/.ssh/*|"$HOME"/.aws/*|"$HOME"/.gnupg/*)
      block "redirection into a credential directory: $t" ;;
    "$HOME"/.*)
      block "redirection into a \$HOME dotfile: $t (shell rc and config files are not editable this way)" ;;
    /etc/*|/usr/*|/bin/*|/sbin/*|/boot/*|/lib/*|/lib64/*)
      block "redirection into a system path: $t" ;;
  esac
  case "$t" in
    *.pem|*.key|.env|.env.*|*/.env|*/.env.*)
      block "redirection into a secret file: $t" ;;
  esac
done

# ------------------------------------------------------------------ 3. gh api
# `gh api` is not read-only. Bash(gh api:*) is in allow for querying; mutating
# verbs, field flags (-f/-F imply POST) and --input must go through a prompt.
if printf '%s' "$CMD" | grep -qE "${CW}(rtk[[:space:]]+)?gh[[:space:]]+api([[:space:]]|\$)"; then
  if printf '%s' "$CMD" | grep -qiE '[[:space:]](-X|--method)[[:space:]]+(POST|PUT|PATCH|DELETE)([[:space:]]|$)'; then
    block "gh api with a mutating method; Bash(gh api:*) only covers reads"
  fi
  # `gh api graphql` always passes the query via -f query=..., for reads as well
  # as writes, so the field-flag rule cannot apply there. Distinguish on the
  # GraphQL operation instead: a mutation is a write, a query is not.
  if printf '%s' "$CMD" | grep -qE "${CW}(rtk[[:space:]]+)?gh[[:space:]]+api[[:space:]]+graphql([[:space:]]|\$)"; then
    if printf '%s' "$CMD" | grep -qiE '(^|[^[:alnum:]_])mutation([^[:alnum:]_]|$)'; then
      block "gh api graphql with a mutation; Bash(gh api:*) only covers reads"
    fi
  elif printf '%s' "$CMD" | grep -qE '[[:space:]](-f|-F|--field|--raw-field|--input)([[:space:]]|=)'; then
    block "gh api with field/input flags implies POST; Bash(gh api:*) only covers reads"
  fi
fi

# ------------------------------------------------------- 4. secret reads via Bash
# The deny list binds the Read tool only -- Read(**/.env), Read(~/.ssh/*) etc.
# do not constrain Bash. Close that asymmetry for the common readers.
READERS='cat|head|tail|less|more|strings|xxd|od|base64|nl|tac'
if printf '%s' "$CMD" | grep -qE "${CW}(rtk[[:space:]]+read|${READERS})([[:space:]]|\$)"; then
  if printf '%s' "$CMD" | grep -qE "[[:space:]/](\.env(\.[^[:space:]]*)?|[^[:space:]]*\.pem|[^[:space:]]*\.key)([[:space:]]|\$)"; then
    block "reading a secret file through Bash; the Read deny rules do not cover Bash"
  fi
  if printf '%s' "$CMD" | grep -qE "[[:space:]](~|${HOME})/\.(ssh|aws|gnupg)/"; then
    block "reading a credential directory through Bash; the Read deny rules do not cover Bash"
  fi
fi

exit 0
