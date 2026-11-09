# Close the gaps in bash-guard.sh and protect-files.sh

Status: draft, 2026-11-09. Not approved, not started. Branch `bash-guard-gaps`.

## Context

`bin/test-hooks` passes all 87 cases. Probes outside the case table found commands that the two
PreToolUse guards let through. These matter more in auto mode. There, a command in `ask` goes to
the auto-mode classifier, not to the user. The hooks are the only check that gives the same
answer every time.

All probes ran as text through the hook, inside the read-only sandbox described below. No probe
command was executed.

| # | Gap | Probe that passes today |
|---|---|---|
| 1 | `gh api` mutating forms. `Bash(gh api:*)` is in `allow`, so these run unprompted | `gh api --method=POST …`, `gh api -XDELETE …`, `gh api -X post …`, `gh api -fbody=x …` |
| 2 | Quote in the middle of a word. Rules 2, 4 and 5 only handle quotes at the word ends | `rm -rf "$HOME"/`, `echo x > "$HOME"/.bashrc`, `echo x > "$HOME/".bashrc`, `cat "$HOME"/.ssh/id_rsa`, `cat ~/".ssh"/id_rsa` |
| 3 | `protect-files.sh` reads only `file_path`. NotebookEdit sends `notebook_path` | NotebookEdit on `.git/x.ipynb` |
| 4 | Rule 2 sees only `>`/`>>`. Rule 4 has a fixed list of readers | `tee -a ~/.bashrc`, `cp evil ~/.bashrc`, `sed -i … ~/.bashrc`, `grep . ~/.ssh/id_rsa`, `cp ~/.ssh/id_rsa /tmp/k`, `awk 1 .env` |
| 5 | `protect-files.sh` matches substrings and misses key files | blocks `.env.example`; allows `key.pem`, `id.key` |

## Safety: no command is ever evaluated

- **The hooks do not execute their input.** `bash-guard.sh` and `protect-files.sh` contain no
  `eval`, `bash -c`, `source` or command substitution of input. They only run `jq`, `awk`, `grep`
  and `case`. The harness passes each case through `jq --arg` to the hook's stdin and never to a
  shell. Keep it that way. Any edit that adds evaluation of `$CMD` is a review blocker.
- **Write cases with the Edit tool only.** Put them in `tests/bash-guard-cases.txt` and in a new
  `tests/protect-files-cases.txt`. Never put a probe command in a Bash tool call, an `echo` or a
  heredoc.
- **Run every test inside a read-only sandbox.** Add a `--sandbox` flag to `bin/test-hooks`. The
  flag re-runs the script under `bwrap` (verified on this machine):

  ```bash
  bwrap --ro-bind / / --tmpfs "$HOME" \
        --ro-bind "$REPO_ROOT" "$REPO_ROOT" \
        --ro-bind "$HOME/.claude/hooks" "$HOME/.claude/hooks" \
        --tmpfs /tmp --dev /dev --proc /proc \
        --unshare-all --die-with-parent --setenv HOME "$HOME" \
        "$0" "${args[@]}"
  ```

  The whole filesystem is read-only, `$HOME` is an empty tmpfs, the network is off, and `HOME`
  keeps its real value, so `$HOME` expansions in the rules still resolve. Even an accidental
  evaluation could not delete or write anything. `bwrap` uses the host's gawk and jq, the same
  binaries the live hooks run on. If `bwrap` is missing, `--sandbox` exits 1. It does not fall
  back to running unsandboxed.
- **Deploy by copying the two hook files, not with `bin/sync-config push`.** That command also
  overwrites the live `settings.json`, which holds machine-specific plugin choices.

## Changes

### A. Shared word parser (fixes gap 2; base for 4)

Rules 2, 4 and 5 each extract arguments their own way, and all three get mid-word quotes wrong.
Replace that with one awk tokenizer over `CMD`. It splits shell words and performs quote
removal, so `"$HOME"/` becomes `$HOME/`. It emits one word per line, plus a flag when the word
began with a quoted `~`, because `"~"/x` does not tilde-expand. Separators `; | & && ||` and `>`
`>>` are their own tokens, and a word-initial `#` ends the line. MASK stays as it is for
command-word detection.

Then:
- **Rule 2** classifies the word after each `>`/`>>`.
- **Rule 4** classifies each non-flag word after a reader.
- **Rule 5** classifies each non-flag word after `rm` (existing `--` and separator logic).

All three share one `expand_home` step for `~`, `$HOME` and `${HOME}`. It skips a word whose
`~` was quoted. A single-quoted `'$HOME'` still expands, deliberately: a false block on the
floor costs less than a miss.

### B. gh api (fix 1)

Match the method case-insensitively: `-X`/`--method`, followed by `=`, whitespace or nothing,
then `POST|PUT|PATCH|DELETE`. Treat any `-f…`/`-F…` word (joined value), `--field`,
`--raw-field` or `--input`, with or without `=`, as a write. Keep the graphql `mutation` rule
as it is.

### C. More write destinations (fix 4a)

Use one `check_dest` function for redirect targets and for these:
- `tee [-a] FILE…`
- the last non-flag word of `cp`, `mv`, `install`, `ln`
- the file words of `sed -i`/`--in-place`
- `dd of=FILE`, `truncate … FILE`

**Open decision 1:** what `check_dest` blocks for the new verbs. Rule 2 blocks every
`$HOME` dotfile. Applying that to `cp` would block `cp config/RTK.md ~/.claude/RTK.md`, which is
normal work here. Recommended: for the new verbs, block credential directories, system paths,
secret files and shell startup files (`.bashrc .bash_profile .bash_login .profile .zshrc
.zprofile .zshenv .bash_logout`). Other dotfiles fall through to `ask`. Leave `>` as it is.

### D. More secret readers (fix 4b)

Add `grep egrep fgrep rg awk gawk sed sort uniq cut diff cmp jq bat cp rsync scp tar zip gzip`
to the readers. The `cp`/`rsync`/`scp` source words are copies of the secret.

**Open decision 2:** some of these readers take a quoted pattern first (`grep`, `rg`, `awk`,
`sed`, `jq`). Case 34 (`grep -n 'cat ~/.ssh/id_rsa' notes.md`) must still pass. Recommended:
for those five, skip the first non-flag word, which is the pattern or program. Treat the rest as
file arguments. `grep -e PAT` and `-f FILE` patterns count as the pattern.

### E. protect-files.sh (fixes 3 and 5)

- Read `.tool_input.file_path // .tool_input.notebook_path`.
- Match path components, not substrings:
  - basename `.env` or `.env.*`, except `.env.example`, `.env.sample` and `.env.template`;
  - basename `package-lock.json`, `*.pem` or `*.key`;
  - any `.git` path component;
  - a path under `$HOME/.ssh`, `$HOME/.aws` or `$HOME/.gnupg`.
- Move the cases into `tests/protect-files-cases.txt` (`<rc><TAB><field><TAB><path>`), in the
  same style as the bash-guard table.

### F. Tests and docs

- Add a block case and a near-miss allow case for every probe in the gap table. Keep all 87
  existing cases unchanged. Near misses to cover:
  - `cp a ~/.claude/x`
  - `gh api -X GET /user`
  - `rm -rf "~"/x`, which is a directory literally named `~`
  - `grep -rn '.env' src/`
  - `tee /tmp/log`
  - `.env.example` through Edit
- Update the rule list in `config/README.md` (lines ~21–22, 235, 260–280) and the "Guard hooks"
  paragraph in `CLAUDE.md`. Add the new regressions to the "past false positives" list if any
  turn up.
- Line 261 of `bash-guard.sh` disables SC2088. A rewrite of rule 5 may remove that line. If so,
  use the escaped-`\~` style that `collect.sh` now uses.

## Order and commits

1. `bin/test-hooks --sandbox` and the protect-files case file. Commit.
2. Add the new cases first, so they fail against current code. Confirm that each one fails.
3. Commit A, B, C+D and E separately. Run `bin/test-hooks --repo --sandbox` after each.
4. Docs. Commit.
5. `/code-review` on the branch, then fix the findings.
6. Copy `config/hooks/{bash-guard,protect-files}.sh` to `~/.claude/hooks/`. Run
   `bin/test-hooks --sandbox` against the live copies.
7. Ask, then merge `--no-ff` and push. Delete this plan in the merge, per `plans/README.md`.

## Verification

- `bin/test-hooks --repo --sandbox` and `bin/test-hooks --sandbox` both report 0 failed. Every
  probe in the gap table is a block case, and every near miss is an allow case.
- `bin/test-hooks --sandbox` with `bwrap` removed from `PATH` exits 1 and runs no cases.
- `shellcheck -S warning config/hooks/*.sh bin/test-hooks` is clean. `uvx codespell` is clean.
- Live smoke test after deployment: an ordinary session still runs `git status`, `rm -rf ./build`
  (prompts), and `cp config/X ~/.claude/X` (prompts, not blocked).

## Out of scope

- Command obfuscation (`base64 -d | sh`, `python -c`, variables built at runtime). These hooks
  catch mistakes; they are not a sandbox.
- The rtk-rewrite friction with auto mode.
- Running `bin/test-hooks` in CI. Worth a separate change, because the GitHub runner's awk may
  not be gawk.
