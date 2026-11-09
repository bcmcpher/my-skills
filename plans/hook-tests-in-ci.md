# Run the hook test suite in CI

Status: draft, 2026-11-09. Not started. Decisions taken 2026-11-09: CI uses the runner's
default awk, without the sandbox, on `ubuntu-26.04`. Awaiting go-ahead.

## Context

`bin/test-hooks` has 198 cases for `bash-guard.sh` and `protect-files.sh`, but only a local run
catches a regression. CI (`.github/workflows/ci.yml`) runs `bin/validate`, shellcheck and a JSON
parse check. Shellcheck does not test behaviour: a hook edit can pass shellcheck and still allow
`rm -rf ~` or block `git status`.

The hooks call `awk` by name. Locally that is GNU Awk 5.1. The tokenizer was written and tested
only under gawk. On 2026-11-09, `ubuntu-latest` resolved to the `ubuntu-26.04` image
(20261101.186.1), the newest LTS. Which awk that image runs by default is not yet confirmed; on
Ubuntu it has been mawk. mawk is installed here at `/usr/bin/mawk`, so the difference can be
tested locally first.

## Safety

The rules from the bash-guard-gaps work still apply. The hooks never evaluate their input, and
the harness passes each case through `jq --arg` to the hook's stdin. Test cases go into
`tests/*-cases.txt` with an editor, never through a shell command. Locally, every run uses
`--sandbox`.

## Changes

### 1. Test the hooks under mawk locally

Add `--awk <path>` to `bin/test-hooks`. It creates a temporary directory with an `awk` symlink
to `<path>`, and puts that directory first on `PATH` for the hook runs. Inside `--sandbox` the
directory goes on the tmpfs `/tmp`.

Run `bin/test-hooks --repo --sandbox --awk /usr/bin/mawk`. Fix any failure in the hooks, not in
the cases. Look for mawk differences in:

- `-v RS='\001'` (whole input as one record);
- regex bracket expressions such as `/[0-9-]/` and `/[ \t\n;&|()<>]/`;
- `length`, `substr` and `index` on multibyte text.

If a difference cannot be fixed cleanly, make the hooks require gawk: call `gawk` by name and
fail open with a stderr warning when it is missing. Decide after the mawk run, not before.

Also run the suite with `--awk /usr/bin/nawk` (the one-true-awk), the awk on macOS. That
check is for information only; the repo does not promise macOS support.

### 2. Add a CI job

Add a `hook-tests` job to `ci.yml`:

```yaml
  hook-tests:
    name: Hook test cases
    runs-on: ubuntu-26.04
    steps:
      - uses: actions/checkout@v4
      - name: Show which awk the hooks will use
        run: readlink -f "$(command -v awk)"
      - name: Run bin/test-hooks against config/hooks/
        run: bin/test-hooks --repo
```

`--repo` tests the tracked copies. The default mode reads `~/.claude/hooks/`, which does not
exist on a runner.

**Decided (2026-11-09):**

- **Runner image: `ubuntu-26.04`, pinned.** It is the newest LTS and is what `ubuntu-latest`
  gives today. Pinning it means a later move of the `-latest` label cannot silently change the
  awk under test; moving to the next LTS is then a deliberate one-line edit. The other jobs
  keep `ubuntu-latest`.
- **awk: the runner's default.** CI then tests the awk a fresh Ubuntu machine has, which is the
  more likely portability failure. Do not install gawk to match this machine. If the default
  turns out to be gawk, run the job's tests once more under mawk (`--awk "$(command -v mawk)"`)
  if mawk is present, so a mawk break is still caught.
- **No `--sandbox` in CI.** The runner is a disposable VM, and the hooks do not evaluate input.
  Local runs keep `--sandbox`.

### 3. Graph gate test

`bin/test-hooks` also runs `graph-update.sh status` from `/tmp`. Confirm it stays silent on a
runner, where `code-review-graph` and `codegraph` are absent. If it is not silent, skip that
part under `CI=true`.

### 4. Docs

- `CLAUDE.md`, "Common commands": add the `--awk` flag.
- `config/README.md`, "Adding a new global hook": say CI runs the cases on every push.
- Close the "Running bin/test-hooks in CI" out-of-scope item that the bash-guard-gaps plan named.

## Order and commits

1. `--awk` flag and the mawk/nawk runs. Commit the flag, then any hook fixes separately.
2. The CI job. Push the branch and confirm the job passes, and that it fails when one case is
   flipped on purpose. Revert the flip before merging.
3. Docs.
4. `/code-review`, then ask before merging.

## Verification

- `bin/test-hooks --repo --sandbox --awk /usr/bin/mawk` reports 0 failed.
- `bin/test-hooks --repo --sandbox` (gawk) still reports 0 failed.
- The `hook-tests` job is green on the branch, and red on a commit with one flipped case.
- shellcheck and codespell are clean.

## Out of scope

- macOS CI runners.
- Moving the hooks off awk.
