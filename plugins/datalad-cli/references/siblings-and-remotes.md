# DataLad Siblings and Remotes Reference

## What is a sibling?

A **sibling** is DataLad's term for a named remote — analogous to a `git remote`. It
stores both the git history and (optionally) annexed file content for a dataset. Every
sibling has a name (e.g., `origin`, `github`, `osf-storage`) and a URL.

---

## `datalad siblings` subcommands

| Subcommand | Purpose |
|------------|---------|
| `datalad siblings` | List all configured siblings (name, URL, +/- indicator) |
| `datalad siblings add -s <name> --url <url>` | Register a new sibling |
| `datalad siblings configure -s <name> ...` | Change a property of an existing sibling |
| `datalad siblings remove -s <name>` | Remove a sibling registration |
| `datalad siblings enable -s <name>` | Enable a special remote after cloning (e.g., S3, OSF) |

### Output format

```
.: origin(+) [https://github.com/user/repo.git (git)]
.: osf-storage(-) [osf://abcde (git-annex)]
```

- `+` means local content can be pushed to this sibling
- `-` means the sibling is read-only or not yet enabled
- The bracketed type indicates `(git)` for a full sibling or `(git-annex)` for an
  annex-only storage sibling

---

## URL formats

| Format | Description |
|--------|-------------|
| `https://github.com/user/repo.git` | HTTPS clone URL (read-only or with credentials) |
| `git@github.com:user/repo.git` | SSH clone URL (read/write) |
| `ssh://user@host/path/to/repo` | Generic SSH |
| `ria+ssh://user@host/path/to/ria-store#~datasetname` | RIA store over SSH |
| `ria+http://ria-server/path/to/ria-store#~datasetname` | RIA store over HTTP |
| `file:///absolute/path/to/store` | Local filesystem path |

### Push URL vs. fetch URL

When a sibling uses HTTPS for reading but SSH for writing, set them separately:
```bash
datalad siblings add -s github \
    --url https://github.com/user/repo.git \
    --pushurl git@github.com:user/repo.git
```

---

## Special remotes

| Remote type | How to add |
|-------------|-----------|
| **OSF** (Open Science Framework) | `datalad siblings add -s osf-storage --url osf://<project-id>` (requires `datalad-osf` extension) |
| **S3** | Configure as a git-annex S3 special remote; enable with `datalad siblings enable -s <name>` after cloning |
| **WebDAV** | `--url webdavs://nextcloud.example.com/remote.php/dav/files/user/dataset` |
| **gin.g-node.org** | Standard SSH/HTTPS sibling; also supports annexed content natively |

After cloning a dataset that had a special remote, run `datalad siblings enable -s <name>`
before trying to `datalad get` content from it.

---

## Publish dependencies (`--publish-depends`)

When a dataset has **two siblings** — a git host (e.g., GitHub) for history and a storage
remote (e.g., OSF, S3, RIA store) for annexed data — DataLad must push annexed content to
storage **before** pushing git history to the git host. Otherwise consumers who clone the
git history will not be able to retrieve file content.

Encode this ordering with `--publish-depends`:

```bash
# Add storage sibling first
datalad siblings add -s osf-storage --url osf://abcde

# Add git sibling with dependency on storage
datalad siblings add -s github \
    --url git@github.com:user/repo.git \
    --publish-depends osf-storage
```

Now `datalad push --to github` automatically pushes annexed content to `osf-storage`
first, then pushes git history to `github`.

---

## Selective content rules: `--annex-wanted` / `--annex-required`

Control which annexed files a sibling wants to store:

```bash
# Only keep files tagged "important"
datalad siblings configure -s origin --annex-wanted 'tag=important'

# Require all files (never drop)
datalad siblings configure -s backup --annex-required 'anything'
```

These use git-annex preferred-content expressions. Common values:
- `anything` — store all annexed content
- `nothing` — store no annexed content (git history only)
- `standard` — default git-annex heuristic
- `include=*.nii.gz` — only NIfTI files

---

## `datalad push --data` modes

| Mode | Behavior |
|------|----------|
| `auto-if-wanted` | Default; pushes annexed content only if the remote's `--annex-wanted` expression matches |
| `nothing` | Push git history only; skip all annexed content |
| `anything` | Push all locally present annexed content regardless of wanted expression |

```bash
datalad push --to github --data nothing       # git history only
datalad push --to osf-storage --data anything # all annexed content
```

---

## `datalad update --follow` policy

When updating subdatasets recursively, `--follow` controls which version of a subdataset
to check out:

| Policy | Behavior |
|--------|----------|
| `parentds` | Pin subdataset to the commit SHA recorded in the superdataset (recommended; preserves reproducibility) |
| `sibling` | Advance subdataset to the sibling's HEAD (may diverge from superdataset pointer) |

Use `--follow=parentds` unless you explicitly want to update the subdataset pointer in
the superdataset.
