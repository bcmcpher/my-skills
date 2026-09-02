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
# command word or a flag, and each has a case in the test matrix.
#
# rtk rewrites commands before this runs in some orderings (git -> rtk git,
# cat -> rtk read), so every command matcher accepts an optional "rtk " prefix.
#
# ---------------------------------------------------------------------------
# The central idea: COMMAND WORDS come from the mask, ARGUMENTS from the text.
#
# Text inside quotes is data. `git commit -m "echo x >> ~/.bashrc is blocked"`
# does not redirect anything, and blocking it is a false positive -- one that
# fires exactly when you are writing about these rules. So matching happens
# against two views of the command:
#
#   CMD   the command with heredoc bodies stripped
#   MASK  the same string with all quoted spans blanked to spaces, character
#         for character, so byte offsets still line up with CMD
#
# A command word found only inside quotes is prose and must not trigger a rule,
# so command words are matched against MASK. An argument inside quotes is still
# an argument -- `cat "$HOME/.ssh/id_rsa"` is a real read -- so once a rule has
# fired on its command word, its arguments are matched against CMD.
# ---------------------------------------------------------------------------

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[ -z "$CMD" ] && exit 0

# Strip heredoc bodies. Their content is DATA, not commands: a commit message
# describing `gh api` rules, or a doc listing `echo x >> ~/.bashrc` as an
# example, is not an invocation.
CMD=$(printf '%s\n' "$CMD" | awk '
  inhd { if ($0 == marker || $0 == marker";") inhd=0; next }
  {
    line=$0
    if (match(line, /<<-?[ \t]*["\047]?[A-Za-z_][A-Za-z0-9_]*["\047]?/)) {
      m=substr(line, RSTART, RLENGTH)
      sub(/^<<-?[ \t]*/, "", m)
      gsub(/["\047]/, "", m)
      marker=m; inhd=1
    }
    print line
  }
')
[ -z "$CMD" ] && exit 0

# Blank every quoted span to spaces of equal length. Quote state carries across
# lines, matching how the shell itself reads a multi-line command. In awk,
# \047 is a single quote -- using the escape avoids unreadable shell quoting.
MASK=$(printf '%s\n' "$CMD" | awk '
  BEGIN { q = 0 }
  {
    n = length($0); out = ""
    for (i = 1; i <= n; i++) {
      c = substr($0, i, 1)
      if (q == 0) {
        if (c == "\047") { q = 1; out = out " "; continue }
        if (c == "\"")   { q = 2; out = out " "; continue }
        out = out c
      } else if (q == 1) {
        if (c == "\047") q = 0
        out = out " "
      } else {
        if (c == "\\") { out = out "  "; i++; continue }
        if (c == "\"") q = 0
        out = out " "
      }
    }
    print out
  }
')

block() { echo "Blocked: $1" >&2; exit 2; }

# Command word: start of string, or after a pipe/semicolon/&&/newline.
CW='(^|[|;&]|[[:space:]])'

# Does a command word appear unquoted? Matched against MASK.
cmdword() { printf '%s' "$MASK" | grep -qE "$1"; }
# Does an argument appear anywhere? Matched against CMD, quotes and all.
arg() { printf '%s' "$CMD" | grep -qE "$1"; }

# ---------------------------------------------------------------- 1. find
# -delete and -exec/-execdir/-ok/-okdir turn an allow-listed read command into
# an arbitrary-deletion primitive.
if cmdword "${CW}(rtk[[:space:]]+)?find([[:space:]]|\$)"; then
  if arg '[[:space:]]-(delete|exec|execdir|ok|okdir)([[:space:]]|$)'; then
    block "find with -delete/-exec is destructive; Bash(find *) only covers searching"
  fi
fi

# ------------------------------------------------------- 2. redirection targets
# Writing via `>` bypasses both Write/Edit sitting in `ask` and the
# protect-files.sh hook. Only sensitive destinations are blocked -- redirecting
# into the worktree or /tmp is ordinary work and stays allowed.
#
# The operator is located in MASK, because `>` inside quotes is a literal
# character and redirects nothing. The target is then read from CMD at the same
# offset, so a quoted destination like `> "$HOME/.bashrc"` is still caught.
TARGETS=$(awk 'NR==FNR { m[FNR]=$0; next }
  {
    cmd = $0; mask = m[FNR]; n = length(mask)
    for (i = 1; i <= n; i++) {
      if (substr(mask, i, 1) != ">") continue
      j = i + 1
      if (substr(mask, j, 1) == ">") j++
      while (j <= n && substr(cmd, j, 1) ~ /[ \t]/) j++
      t = ""; qc = substr(cmd, j, 1)
      if (qc == "\"" || qc == "\047") {
        j++
        while (j <= n && substr(cmd, j, 1) != qc) { t = t substr(cmd, j, 1); j++ }
      } else {
        while (j <= n && substr(cmd, j, 1) !~ /[ \t;&|<>()]/) { t = t substr(cmd, j, 1); j++ }
      }
      if (t != "") print t
      i = j
    }
  }' <(printf '%s\n' "$MASK") <(printf '%s\n' "$CMD"))

while IFS= read -r t; do
  [ -z "$t" ] && continue
  case "$t" in
    /dev/null|/dev/stdout|/dev/stderr) continue ;;
  esac
  # Expand the two forms a destination is normally written in. Without this,
  # `> "$HOME/.bashrc"` reads as a literal path and matches nothing.
  case "$t" in
    "~"*)        t="${HOME}${t#\~}" ;;
    '$HOME'*)    t="${HOME}${t#\$HOME}" ;;
    '${HOME}'*)  t="${HOME}${t#\$\{HOME\}}" ;;
  esac
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
done <<< "$TARGETS"

# ------------------------------------------------------------------ 3. gh api
# `gh api` is not read-only. Bash(gh api:*) is in allow for querying; mutating
# verbs, field flags (-f/-F imply POST) and --input must go through a prompt.
if cmdword "${CW}(rtk[[:space:]]+)?gh[[:space:]]+api([[:space:]]|\$)"; then
  if arg '[[:space:]](-X|--method)[[:space:]]+["\x27]?(POST|PUT|PATCH|DELETE)'; then
    block "gh api with a mutating method; Bash(gh api:*) only covers reads"
  fi
  # `gh api graphql` always passes the query via -f query=..., for reads as well
  # as writes, so the field-flag rule cannot apply there. Distinguish on the
  # GraphQL operation instead: a mutation is a write, a query is not. The query
  # body is quoted, so this one deliberately reads CMD.
  if cmdword "${CW}(rtk[[:space:]]+)?gh[[:space:]]+api[[:space:]]+graphql([[:space:]]|\$)"; then
    if arg '(^|[^[:alnum:]_])mutation([^[:alnum:]_]|$)'; then
      block "gh api graphql with a mutation; Bash(gh api:*) only covers reads"
    fi
  elif arg '[[:space:]](-f|-F|--field|--raw-field|--input)([[:space:]]|=)'; then
    block "gh api with field/input flags implies POST; Bash(gh api:*) only covers reads"
  fi
fi

# ------------------------------------------------------- 4. secret reads via Bash
# The deny list binds the Read tool only -- Read(**/.env), Read(~/.ssh/*) etc.
# do not constrain Bash. Close that asymmetry for the common readers.
READERS='cat|head|tail|less|more|strings|xxd|od|base64|nl|tac'
if cmdword "${CW}(rtk[[:space:]]+read|${READERS})([[:space:]]|\$)"; then
  if arg "[[:space:]/\"\x27](\.env(\.[^[:space:]\"\x27]*)?|[^[:space:]\"\x27]*\.pem|[^[:space:]\"\x27]*\.key)([[:space:]\"\x27]|\$)"; then
    block "reading a secret file through Bash; the Read deny rules do not cover Bash"
  fi
  if arg "[[:space:]\"\x27](~|\\\$HOME|\\\$\{HOME\}|${HOME})/\.(ssh|aws|gnupg)/"; then
    block "reading a credential directory through Bash; the Read deny rules do not cover Bash"
  fi
fi

exit 0
