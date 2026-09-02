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
#
# A comment is blanked the same way, for the same reason quoted spans are: the
# text after `#` is prose, not an invocation. `echo hi # cat ~/.ssh/id_rsa` reads
# no secret. Only a WORD-INITIAL `#` starts a comment, which is also how the
# shell reads it -- the fragment in `https://example.com/a#frag` is not one.
# A comment ends at the newline, so `q` is deliberately left untouched.
MASK=$(printf '%s\n' "$CMD" | awk '
  BEGIN { q = 0 }
  {
    n = length($0); out = ""
    for (i = 1; i <= n; i++) {
      c = substr($0, i, 1)
      if (q == 0) {
        if (c == "#" && (i == 1 || substr($0, i - 1, 1) ~ /[ \t]/)) {
          while (i <= n) { out = out " "; i++ }
          break
        }
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

# ------------------------------------------------------------------ 5. rm floor
# Ordinary `rm` lives in `ask` -- it prompts, and you can approve it. This rule
# is only the floor beneath that prompt: the handful of targets that should stay
# impossible no matter what the prompt says.
#
# The permission globs cannot express this. `Bash(rm -rf *)` is anchored to the
# start of the command string, so `cd x && rm -rf /`, `rm -fr /`, `rm -Rf /` and
# `xargs rm -rf` all walk past it. Matching an argument position catches every
# spelling and every position in a pipeline.
#
# Two deliberate narrowings, both about false positives:
#
#   * The match is on the WHOLE normalised target, never a prefix. `rm -rf
#     /tmp/scratch`, `rm -rf /tmp/*` and `rm -rf ~/Projects/x/node_modules` are
#     ordinary work and must pass. Only the bare root itself is a floor.
#   * Bare `.` is not blocked; `..` is. `rm -rf .` inside a build or scratch
#     directory is a real idiom, `rm -rf ..` never is. `.` falls through to ask.
#
# The floor covers the mount roots `/home /srv /mnt /media` as well as the system
# directories. `$HOME` is a floor, so its parent has to be one too -- `rm -rf
# /home` takes every account with it. Whole-target matching keeps the cost at
# nothing: `rm -rf /mnt/scratch/build` still passes.
#
# The credential-directory clause is narrower than rule 2's, which blocks
# redirection into ANY $HOME dotfile. Blocking `rm ~/.cache/foo` would be pure
# friction, so rm floors only .ssh/.aws/.gnupg. The asymmetry is intended.
#
# Flags are not required for a block. `rm /etc` fails on its own anyway, and not
# special-casing -r/-f keeps the rule short and impossible to spell around.
if cmdword "${CW}(rtk[[:space:]]+)?rm([[:space:]]|\$)"; then
  # Targets are the non-flag words after each `rm`, with `--` ending the flags.
  # Read from CMD, not MASK: a quoted "$HOME" is still a real target.
  RM_TARGETS=$(printf '%s\n' "$CMD" | awk '
    { line = $0
      # Space the separators out before splitting. They are punctuation, not
      # words, and `rm -rf ./build;ls /` glues one to the previous word -- which
      # left `inrm` set and scanned `ls`'"'"'s argument as an rm target, blocking
      # an ordinary command list. `&&` and `||` become two tokens, each of which
      # the separator test below already matches.
      gsub(/[;&|]/, " \\& ", line)
      n = split(line, w, /[ \t]+/)
      inrm = 0; endflags = 0
      for (i = 1; i <= n; i++) {
        t = w[i]
        # Rest of the line is a comment. MASK already stops `cmdword` firing on
        # a commented-out rm; this is the mirror case, a real rm whose trailing
        # comment must not be read as arguments.
        if (t ~ /^#/) break
        if (t ~ /^(rtk|sudo|xargs|env)$/) continue
        if (t == "rm") { inrm = 1; endflags = 0; continue }
        if (!inrm) continue
        # A shell separator ends this rm invocation.
        if (t ~ /^(\||;|&&|\|\||&)$/) { inrm = 0; continue }
        if (t == "--") { endflags = 1; continue }
        if (!endflags && t ~ /^-/) continue
        gsub(/^["\047]|["\047]$/, "", t)
        if (t != "") print t
      } }')

  while IFS= read -r t; do
    [ -z "$t" ] && continue
    # Same three expansions rule 2 uses for redirection destinations. Without
    # them `rm -rf "$HOME"` reads as a literal path and matches nothing.
    case "$t" in
      "~")         t="$HOME" ;;
      "~/"*)       t="${HOME}${t#\~}" ;;
      '$HOME')     t="$HOME" ;;
      '$HOME/'*)   t="${HOME}${t#\$HOME}" ;;
      '${HOME}')   t="$HOME" ;;
      '${HOME}/'*) t="${HOME}${t#\$\{HOME\}}" ;;
    esac
    # Strip a single trailing slash so `/usr/` and `/usr` are one case. Not
    # applied to "/" itself, which would otherwise become the empty string.
    [ "$t" != "/" ] && t="${t%/}"

    case "$t" in
      /|"/*")
        block "rm targeting the filesystem root: $t" ;;
      "$HOME"|"$HOME/*")
        block "rm targeting your home directory: $t" ;;
      /etc|/usr|/var|/bin|/sbin|/boot|/lib|/lib64|/opt|/root|/home|/srv|/mnt|/media|"/etc/*"|"/usr/*"|"/var/*"|"/bin/*"|"/sbin/*"|"/boot/*"|"/lib/*"|"/lib64/*"|"/opt/*"|"/root/*"|"/home/*"|"/srv/*"|"/mnt/*"|"/media/*")
        block "rm targeting a system directory: $t" ;;
      ..)
        block "rm targeting the parent directory: $t" ;;
      "$HOME"/.ssh|"$HOME"/.ssh/*|"$HOME"/.aws|"$HOME"/.aws/*|"$HOME"/.gnupg|"$HOME"/.gnupg/*)
        block "rm targeting a credential directory: $t" ;;
    esac
  done <<< "$RM_TARGETS"
fi

exit 0
