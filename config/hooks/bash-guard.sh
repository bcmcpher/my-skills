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

# --------------------------------------------- 2b. write destinations of tools
# tee, cp, mv, install, ln, sed -i, dd of= and truncate write files too. These
# get a NARROWER list than `>`: copying into ~/.claude/ or another dotfile is
# normal work here and falls through to the prompt. Blocked are credential
# directories, system paths, secret files, and the shell startup files, which
# run code in every new shell.
check_dest() { # <tilde-ok> <word>
  case "$2" in /dev/null|/dev/stdout|/dev/stderr) return ;; esac
  expand_home "$1" "$2"
  is_cred_path "$X" && block "write into a credential directory: $X"
  case "$X" in
    /etc/*|/usr/*|/bin/*|/sbin/*|/boot/*|/lib/*|/lib64/*)
      block "write into a system path: $X" ;;
    "$HOME"/.bashrc|"$HOME"/.bash_profile|"$HOME"/.bash_login|"$HOME"/.bash_logout|"$HOME"/.profile|"$HOME"/.zshrc|"$HOME"/.zprofile|"$HOME"/.zshenv)
      block "write into a shell startup file: $X" ;;
  esac
  is_secret_file "$X" && block "write into a secret file: $X"
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
#
# `gh api graphql` always passes the query via -f query=..., for reads as well
# as writes, so the field-flag rule cannot apply there. Distinguish on the
# GraphQL operation instead: a mutation is a write, a query is not. The query
# body is quoted, so this one deliberately reads CMD.
GH_GRAPHQL=0
if cmdword "${CW}(rtk[[:space:]]+)?gh[[:space:]]+api[[:space:]]+graphql([[:space:]]|\$)"; then
  GH_GRAPHQL=1
  if arg '(^|[^[:alnum:]_])mutation([^[:alnum:]_]|$)'; then
    block "gh api graphql with a mutation; Bash(gh api:*) only covers reads"
  fi
fi

# The method and field flags are read from the words of a `gh api` scope, so
# every spelling counts: `-X POST`, `-XPOST`, `--method=post`, `-fbody=x`,
# `--input=f.json`. An explicit `-X GET` with fields is a read: gh then sends
# the fields as query parameters, the usual way to call the search endpoints.
check_gh() {
  local e w method="" want=0 fields=0
  [ "${SW[0]#*$'\t'}" = api ] || return 0
  for e in "${SW[@]:1}"; do
    w=${e#*$'\t'}
    if [ $want = 1 ]; then method=$w; want=0; continue; fi
    case "$w" in
      -X|--method) want=1 ;;
      --method=*)  method=${w#--method=} ;;
      -X*)         method=${w#-X} ;;
      -f*|-F*|--field|--field=*|--raw-field|--raw-field=*|--input|--input=*) fields=1 ;;
    esac
  done
  method=${method^^}
  case "$method" in
    POST|PUT|PATCH|DELETE) block "gh api with a mutating method; Bash(gh api:*) only covers reads" ;;
  esac
  if [ $fields = 1 ] && [ $GH_GRAPHQL = 0 ] && [ "$method" != GET ]; then
    block "gh api with field/input flags implies POST; Bash(gh api:*) only covers reads"
  fi
}

# ------------------------------------------------------------ word-level rules
# Walk TOKENS. An unquoted word naming a known command opens a SCOPE, and the
# scope's words are collected up to the next separator. Only the first known
# command in a segment opens one, so an argument that happens to be a command
# name (`cp cat ~/x`) does not hide the real command. Prefix words such as
# `sudo`, `xargs`, `env` and `rtk` name no scope and are passed over.
# `>` and `<` targets are checked wherever they appear.

#
# Scope names, and what each checks:
#
#   rm                     every operand against the rm floor (rule 5)
#   gh                     `gh api` method and field flags (rule 3)
#   cat (the plain readers) every operand as a secret read (rule 4)
#   grep rg awk sed jq     the same, except the first operand: that is the
#                          pattern or program, unless -e/-f supplied it.
#                          `grep -n 'cat ~/.ssh/id_rsa' notes.md` reads notes.md.
#                          sed -i also checks its files as write destinations.
#   cp                     every operand as a read (a copy of a secret is a read
#                          of it), and the destination as a write (rule 2b)
#   mv install ln          the destination as a write
#   tee truncate           every operand as a write
#   rsync scp              every operand as a read
#   dd                     of= as a write, if= as a read
scope_name() { # <word> <previous word>: set N
  case "$1" in
    rm|gh|grep|rg|awk|sed|jq|cp|mv|install|ln|tee|truncate|rsync|scp|dd) N=$1 ;;
    egrep|fgrep) N="grep" ;;
    gawk)        N="awk" ;;
    cat|head|tail|less|more|strings|xxd|od|base64|nl|tac|sort|uniq|cut|diff|cmp|bat|zip|gzip|tar) N="cat" ;;
    read) if [ "$2" = rtk ]; then N="cat"; else N=""; fi ;;
    *)   N="" ;;
  esac
}

# Short options that take a value, per scope. In a cluster, the first such
# letter takes the rest of the word, or the next word if it is last (`-rnf
# pats`). Missing an option here only means its value is checked as an
# operand; a wrong entry could hide an operand, so the lists stay small.
short_values() {
  case "$1" in
    grep)    V="efmABCdD" ;;
    rg)      V="efmABCgtTMjE" ;;
    awk)     V="Fvf" ;;
    sed)     V="efl" ;;
    jq)      V="fL" ;;
    cp|mv|ln) V="tS" ;;
    install) V="tmogS" ;;
    truncate) V="sr" ;;
    rsync)   V="eT" ;;
    scp)     V="iFoPcJlS" ;;
    *)       V="" ;;
  esac
}

# Long options that take the NEXT word as a value (the `--opt=value` form needs
# no entry). Sets need (words to skip), kind (t: the value is a target
# directory) and PAT (the pattern was given by option).
long_option() { # <scope> <option>
  case "$1:$2" in
    sed:--in-place) INPLACE=1 ;;
    grep:--regexp|grep:--file|rg:--regexp|rg:--file|sed:--expression|sed:--file|awk:--file|jq:--from-file)
      PAT=1; need=1 ;;
    grep:--max-count|grep:--context|grep:--after-context|grep:--before-context|rg:--max-count|rg:--context|rg:--glob|rg:--type|awk:--assign|awk:--field-separator|jq:--indent|truncate:--size|truncate:--reference|install:--mode|install:--owner|install:--group)
      need=1 ;;
    jq:--arg|jq:--argjson|jq:--slurpfile|jq:--rawfile)
      need=2 ;;
    cp:--target-directory|mv:--target-directory|ln:--target-directory|install:--target-directory)
      need=1; kind=t ;;
  esac
}

# Split SW into operands P (tilde flags in PT), and note PAT, INPLACE (sed -i)
# and TDIR (a -t/--target-directory destination).
split_scope() {
  local e t w s c i need=0 kind="" endflags=0
  P=(); PT=(); PAT=0; INPLACE=0; TDIR=""; TDIRT=0
  short_values "$scope"
  for e in "${SW[@]}"; do
    t=${e%%$'\t'*}; w=${e#*$'\t'}
    if [ $need -gt 0 ]; then
      need=$((need - 1))
      if [ "$kind" = t ]; then TDIR=$w; TDIRT=$t; fi
      continue
    fi
    kind=""
    if [ $endflags = 0 ]; then
      case "$w" in
        --) endflags=1; continue ;;
        --*=*)
          case "$scope:${w%%=*}" in
            sed:--in-place) INPLACE=1 ;;
            grep:--regexp|grep:--file|rg:--regexp|rg:--file|sed:--expression|sed:--file|awk:--file|jq:--from-file) PAT=1 ;;
            cp:--target-directory|mv:--target-directory|ln:--target-directory|install:--target-directory)
              TDIR=${w#*=}; TDIRT=0 ;;
          esac
          continue ;;
        --?*) long_option "$scope" "$w"; continue ;;
        -?*)
          s=${w#-}
          for ((i = 0; i < ${#s}; i++)); do
            c=${s:i:1}
            # sed -i[SUFFIX]: the rest of the cluster is the backup suffix.
            if [ "$scope" = sed ] && [ "$c" = i ]; then INPLACE=1; break; fi
            case "$V" in
              *"$c"*)
                case "$scope:$c" in grep:[ef]|rg:[ef]|sed:[ef]|awk:f|jq:f) PAT=1 ;; esac
                if [ $((i + 1)) -eq ${#s} ]; then
                  need=1; [ "$c" = t ] && kind=t
                elif [ "$c" = t ]; then
                  TDIR=${s:i+1}; TDIRT=0
                fi
                break ;;
            esac
          done
          continue ;;
      esac
    fi
    [ -z "$w" ] && continue
    P+=("$w"); PT+=("$t")
  done
}

finish_scope() {
  local i n start v
  case "$scope" in
    "") return ;;
    gh) check_gh ;;
    *)
      split_scope
      n=${#P[@]}
      case "$scope" in
        rm)
          for ((i = 0; i < n; i++)); do check_rm "${PT[i]}" "${P[i]}"; done ;;
        cat|rsync|scp|cp)
          for ((i = 0; i < n; i++)); do check_read "${PT[i]}" "${P[i]}"; done ;;
        grep|rg|awk|sed|jq)
          start=$((1 - PAT))
          for ((i = start; i < n; i++)); do
            check_read "${PT[i]}" "${P[i]}"
            [ $INPLACE = 1 ] && check_dest "${PT[i]}" "${P[i]}"
          done ;;
        tee|truncate)
          for ((i = 0; i < n; i++)); do check_dest "${PT[i]}" "${P[i]}"; done ;;
        dd)
          # Bash tilde-expands after `=` in an assignment-shaped word, so
          # of=~/x does reach $HOME.
          for ((i = 0; i < n; i++)); do
            v=${P[i]#*=}
            case "${P[i]}" in
              of=*) check_dest 1 "$v" ;;
              if=*) check_read 1 "$v" ;;
            esac
          done ;;
      esac
      # The destination of cp, mv, install and ln: -t DIR, else the last
      # operand when there are at least two.
      case "$scope" in
        cp|mv|install|ln)
          if [ -n "$TDIR" ]; then
            check_dest "$TDIRT" "$TDIR"
          elif [ "$n" -ge 2 ]; then
            check_dest "${PT[n-1]}" "${P[n-1]}"
          fi ;;
      esac ;;
  esac
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
