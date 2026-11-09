#!/bin/bash
# bash-guard.sh — PreToolUse hook for Bash.
#
# Covers classes of command that the permission glob syntax cannot express,
# so that Bash(find *), Bash(echo *) and Bash(gh api:*) can stay in `allow`
# without their sharp edges.
#
# Every rule matches an ARGUMENT POSITION, never raw command text. The deleted
# git-guard.sh matched ".git/" anywhere in the command and so blocked the
# ordinary idiom `find . -not -path "./.git/*"`. Rules here are anchored to a
# command word or a flag, and each has a case in the test matrix.
#
# This hook NEVER evaluates its input. It only pattern-matches the command text
# with jq, awk, grep and `case`. Any change that runs, sources or expands $CMD
# is a review blocker.
#
# rtk rewrites commands before this runs in some orderings (git -> rtk git,
# cat -> rtk read), so every command matcher accepts an optional "rtk " prefix.
#
# ---------------------------------------------------------------------------
# Two views of the command:
#
#   CMD     the command with heredoc bodies stripped
#   TOKENS  CMD split into shell words, one per line, with quote removal done
#           (`"$HOME"/.bashrc` becomes `$HOME/.bashrc`). Separators, `>` and
#           `<` are their own tokens, and a word-initial `#` ends the line.
#
# Text inside quotes is data. `git commit -m "echo x >> ~/.bashrc is blocked"`
# does not redirect anything, and blocking it is a false positive -- one that
# fires exactly when you are writing about these rules. So a word that
# contained any quoting never counts as a COMMAND word, and quoted `>` or `;`
# are ordinary characters. An ARGUMENT inside quotes is still an argument --
# `cat "$HOME/.ssh/id_rsa"` is a real read -- so arguments are classified after
# quote removal.
#
# Rules 1 and 3's graphql check still use MASK, CMD with quoted spans blanked.
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
# text after `#` is prose, not an invocation. Only a WORD-INITIAL `#` starts a
# comment, which is also how the shell reads it -- the fragment in
# `https://example.com/a#frag` is not one.
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

# Shell word splitter. Output, one token per line:
#
#   S<TAB><sep>    a separator: newline ; & | ( ) ` $(
#   R<TAB>>        an output redirection (> >> >| &>); the next word is its file
#   I<TAB><        an input redirection (< << <<<); the next word is its file
#   <q><t><TAB>w   a word after quote removal. <q> is 1 if any part of it was
#                  quoted. <t> is 1 if it begins with a tilde the shell would
#                  expand: an unquoted `~` followed by an unquoted `/` or by
#                  nothing. `"~"/x` names a directory literally called `~`.
#
# `2>file` drops the fd number, and `>&2` is an fd duplication, not a file.
# A newline inside a quoted word becomes a space, keeping one token per line.
TOKENS=$(printf '%s' "$CMD" | awk -v RS='\001' '
  function emit(k, x) { gsub(/\n/, " ", x); print k "\t" x }
  function addc(ch, quoted) {
    pos++
    if (pos == 1) q1 = quoted; else if (pos == 2) q2 = quoted
    if (quoted) hq = 1
    w = w ch; inw = 1
  }
  function reset() { inw = 0; w = ""; hq = 0; q1 = 0; q2 = 0; pos = 0 }
  function endw(  tl) {
    if (inw) {
      tl = (substr(w, 1, 1) == "~" && !q1 && (pos == 1 || (substr(w, 2, 1) == "/" && !q2)))
      emit((hq ? "1" : "0") (tl ? "1" : "0"), w)
    }
    reset()
  }
  { s = s $0 }
  END {
    n = length(s); i = 1; q = 0; reset()
    while (i <= n) {
      c = substr(s, i, 1)
      if (q == 1) {
        if (c == "\047") q = 0; else addc(c, 1)
        i++; continue
      }
      if (q == 2) {
        if (c == "\"") { q = 0; i++; continue }
        if (c == "\\" && i < n && index("\"\\$`\n", substr(s, i + 1, 1))) {
          d = substr(s, i + 1, 1); if (d != "\n") addc(d, 1); i += 2; continue
        }
        addc(c, 1); i++; continue
      }
      if (c == "\047") { q = 1; inw = 1; hq = 1; i++; continue }
      if (c == "\"")   { q = 2; inw = 1; hq = 1; i++; continue }
      if (c == "\\") {
        if (i < n) { d = substr(s, i + 1, 1); if (d != "\n") addc(d, 1) }
        i += 2; continue
      }
      if (c == " " || c == "\t") { endw(); i++; continue }
      if (c == "#" && !inw) { while (i <= n && substr(s, i, 1) != "\n") i++; continue }
      if (c == "&" && substr(s, i + 1, 1) == ">") {
        endw(); emit("R", ">"); i += 2
        if (substr(s, i, 1) == ">") i++
        continue
      }
      if (c == "$" && substr(s, i + 1, 1) == "(") { endw(); emit("S", "$("); i += 2; continue }
      if (c == "\n" || c == ";" || c == "&" || c == "|" || c == "(" || c == ")" || c == "`") {
        endw(); emit("S", c); i++; continue
      }
      if (c == ">") {
        if (inw && !hq && w ~ /^[0-9]+$/) reset(); else endw()
        i++
        if (substr(s, i, 1) == ">" || substr(s, i, 1) == "|") i++
        if (substr(s, i, 1) == "&") { i++; while (substr(s, i, 1) ~ /[0-9-]/) i++; continue }
        emit("R", ">"); continue
      }
      if (c == "<") {
        endw(); i++
        while (substr(s, i, 1) == "<") i++
        emit("I", "<"); continue
      }
      addc(c, 0); i++
    }
    endw()
  }')

block() { echo "Blocked: $1" >&2; exit 2; }

# Command word: start of string, or after a pipe/semicolon/&&/newline.
CW='(^|[|;&]|[[:space:]])'

# Does a command word appear unquoted? Matched against MASK.
cmdword() { printf '%s' "$MASK" | grep -qE "$1"; }
# Does an argument appear anywhere? Matched against CMD, quotes and all.
arg() { printf '%s' "$CMD" | grep -qE "$1"; }

# ---------------------------------------------------------- path classifiers
# expand_home <tilde-ok> <word>: set X to the word with a leading ~, $HOME or
# ${HOME} resolved. Without this, `> "$HOME/.bashrc"` reads as a literal path
# and matches nothing. A single-quoted '$HOME' cannot be told apart after quote
# removal and is expanded too, deliberately: a false block costs less than a
# miss. The `\~` patterns match a literal tilde in untrusted text.
expand_home() {
  X=$2
  if [ "$1" = 1 ]; then
    case "$X" in
      \~)    X=$HOME ;;
      \~/*)  X="${HOME}${X#\~}" ;;
    esac
  fi
  case "$X" in
    '$HOME'|'$HOME/'*)     X="${HOME}${X#\$HOME}" ;;
    '${HOME}'|'${HOME}/'*) X="${HOME}${X#\$\{HOME\}}" ;;
  esac
}

is_cred_path() {
  case "$1" in
    "$HOME"/.ssh|"$HOME"/.ssh/*|"$HOME"/.aws|"$HOME"/.aws/*|"$HOME"/.gnupg|"$HOME"/.gnupg/*) return 0 ;;
  esac
  return 1
}

# Secret by basename. The example/sample/template forms of .env hold no secrets
# and are committed to repos on purpose.
is_secret_file() {
  case "${1##*/}" in
    .env.example|.env.sample|.env.template) return 1 ;;
    .env|.env.*|*.pem|*.key) return 0 ;;
  esac
  return 1
}

# ------------------------------------------------------- 2. redirection targets
# Writing via `>` bypasses both Write/Edit sitting in `ask` and the
# protect-files.sh hook. Only sensitive destinations are blocked -- redirecting
# into the worktree or /tmp is ordinary work and stays allowed.
check_redirect() { # <tilde-ok> <word>
  case "$2" in /dev/null|/dev/stdout|/dev/stderr) return ;; esac
  expand_home "$1" "$2"
  is_cred_path "$X" && block "redirection into a credential directory: $X"
  case "$X" in
    "$HOME"/.*)
      block "redirection into a \$HOME dotfile: $X (shell rc and config files are not editable this way)" ;;
    /etc/*|/usr/*|/bin/*|/sbin/*|/boot/*|/lib/*|/lib64/*)
      block "redirection into a system path: $X" ;;
  esac
  case "${X##*/}" in
    *.pem|*.key|.env|.env.*) block "redirection into a secret file: $X" ;;
  esac
}

# ------------------------------------------------------- 4. secret reads via Bash
# The deny list binds the Read tool only -- Read(**/.env), Read(~/.ssh/*) etc.
# do not constrain Bash. Close that asymmetry for the common readers.
check_read() { # <tilde-ok> <word>
  expand_home "$1" "$2"
  is_secret_file "$X" && block "reading a secret file through Bash; the Read deny rules do not cover Bash: $X"
  is_cred_path "$X" && block "reading a credential directory through Bash; the Read deny rules do not cover Bash: $X"
}

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
check_rm() { # <tilde-ok> <word>
  expand_home "$1" "$2"
  # Strip a single trailing slash so `/usr/` and `/usr` are one case. Not
  # applied to "/" itself, which would otherwise become the empty string.
  [ "$X" != "/" ] && X="${X%/}"
  case "$X" in
    /|"/*")
      block "rm targeting the filesystem root: $X" ;;
    "$HOME"|"$HOME/*")
      block "rm targeting your home directory: $X" ;;
    /etc|/usr|/var|/bin|/sbin|/boot|/lib|/lib64|/opt|/root|/home|/srv|/mnt|/media|"/etc/*"|"/usr/*"|"/var/*"|"/bin/*"|"/sbin/*"|"/boot/*"|"/lib/*"|"/lib64/*"|"/opt/*"|"/root/*"|"/home/*"|"/srv/*"|"/mnt/*"|"/media/*")
      block "rm targeting a system directory: $X" ;;
    ..)
      block "rm targeting the parent directory: $X" ;;
  esac
  is_cred_path "$X" && block "rm targeting a credential directory: $X"
}

# ---------------------------------------------------------------- 1. find
# -delete and -exec/-execdir/-ok/-okdir turn an allow-listed read command into
# an arbitrary-deletion primitive.
if cmdword "${CW}(rtk[[:space:]]+)?find([[:space:]]|\$)"; then
  if arg '[[:space:]]-(delete|exec|execdir|ok|okdir)([[:space:]]|$)'; then
    block "find with -delete/-exec is destructive; Bash(find *) only covers searching"
  fi
fi

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

# ------------------------------------------------------------ word-level rules
# Walk TOKENS. An unquoted word naming a known command opens a SCOPE, and the
# scope's words are collected up to the next separator. Only the first known
# command in a segment opens one, so an argument that happens to be a command
# name (`cp cat ~/x`) does not hide the real command. Prefix words such as
# `sudo`, `xargs`, `env` and `rtk` name no scope and are passed over.
# `>` and `<` targets are checked wherever they appear.

scope_name() { # <word> <previous word>: set N
  case "$1" in
    rm)  N="rm" ;;
    cat|head|tail|less|more|strings|xxd|od|base64|nl|tac) N="read" ;;
    read) if [ "$2" = rtk ]; then N="read"; else N=""; fi ;;
    *)   N="" ;;
  esac
}

# Each SW entry is "<tilde-ok><TAB><word>".
finish_scope() {
  local e t w endflags=0
  for e in "${SW[@]}"; do
    t=${e%%$'\t'*}; w=${e#*$'\t'}
    if [ $endflags = 0 ]; then
      [ "$w" = "--" ] && { endflags=1; continue; }
      case "$w" in -?*) continue ;; esac
    fi
    [ -z "$w" ] && continue
    case "$scope" in
      rm)   check_rm "$t" "$w" ;;
      read) check_read "$t" "$w" ;;
    esac
  done
  scope=""; SW=()
}

scope=""; SW=(); prevw=""; pending=""
while IFS= read -r tok; do
  [ -z "$tok" ] && continue
  k=${tok%%$'\t'*}; w=${tok#*$'\t'}
  case "$k" in
    S)   finish_scope; pending=""; prevw=""; continue ;;
    R|I) pending=$k; continue ;;
  esac
  tl=${k:1:1}
  if [ -n "$pending" ]; then
    if [ "$pending" = R ]; then check_redirect "$tl" "$w"; else check_read "$tl" "$w"; fi
    pending=""; continue
  fi
  if [ -z "$scope" ] && [ "${k:0:1}" = 0 ]; then
    scope_name "$w" "$prevw"
    if [ -n "$N" ]; then scope=$N; prevw=$w; continue; fi
  fi
  [ -n "$scope" ] && SW+=("$tl"$'\t'"$w")
  prevw=$w
done <<< "$TOKENS"
finish_scope

exit 0
