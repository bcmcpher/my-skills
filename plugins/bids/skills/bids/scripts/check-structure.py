#!/usr/bin/env python3
"""Lightweight BIDS structural checker — no external dependencies.

Covers the most common compliance issues when bids-validator is unavailable:
  - Dataset-level required/recommended files
  - Subject and session directory naming
  - Datatype directory names
  - Filename entity ordering, label format, and valid suffixes
  - DWI companion file presence (.bvec/.bval)
  - JSON sidecar existence for each NIfTI
  - BOLD sidecars: TaskName and RepetitionTime presence
  - Field map sidecars: IntendedFor presence and path resolution

Usage: check-structure.py <dataset-path>

Exit codes: 0 = no errors, 1 = errors found
"""

import json
import os
import re
import sys
from pathlib import Path

# ── Spec constants ─────────────────────────────────────────────────────────────

VALID_DATATYPES = {
    "anat", "func", "dwi", "fmap", "perf",
    "eeg", "ieeg", "meg", "pet", "beh", "micr", "motion", "nirs", "mrs",
}

# Canonical entity order (key → position)
ENTITY_ORDER = {
    "sub": 1, "ses": 2, "sample": 3, "task": 4, "acq": 5, "ce": 6,
    "rec": 7, "dir": 8, "run": 9, "mod": 10, "echo": 11, "flip": 12,
    "inv": 13, "mt": 14, "part": 15, "proc": 16, "hemi": 17, "space": 18,
    "res": 19, "den": 20, "label": 21, "split": 22, "desc": 23,
}

# Suffixes that require the task entity
TASK_REQUIRED_SUFFIXES = {"bold", "cbv", "phase", "events", "physio", "stim", "beh"}

# Suffixes that require .bvec / .bval companions (NIfTI only)
DWI_SUFFIXES = {"dwi"}

# Valid func suffixes (used to identify BOLD sidecars to check)
FUNC_SUFFIXES = {"bold", "cbv", "sbref"}

LABEL_RE = re.compile(r"^[A-Za-z0-9]+$")
SUB_RE   = re.compile(r"^sub-[A-Za-z0-9]+$")
SES_RE   = re.compile(r"^ses-[A-Za-z0-9]+$")


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_filename(name):
    """Return (entities_in_order, suffix, ext) or None if unparseable."""
    stem, *exts = name.split(".")
    ext = "." + ".".join(exts) if exts else ""
    parts = stem.split("_")
    if len(parts) < 2:
        return None
    suffix = parts[-1]
    entities = []
    for part in parts[:-1]:
        if "-" in part:
            key, val = part.split("-", 1)
            entities.append((key, val))
        else:
            return None  # bare token that isn't the suffix
    return entities, suffix, ext


class Report:
    def __init__(self, dataset):
        self.dataset = dataset
        self.errors   = []
        self.warnings = []

    def error(self, msg, path=None):
        tag = f"  {path}: " if path else "  "
        self.errors.append(f"{tag}{msg}")

    def warn(self, msg, path=None):
        tag = f"  {path}: " if path else "  "
        self.warnings.append(f"{tag}{msg}")

    def print_report(self):
        header = f"BIDS Structural Check: {self.dataset}  [fallback — install bids-validator for full validation]"
        print(header)
        print("=" * len(header))
        print()

        if self.errors:
            print(f"ERRORS ({len(self.errors)}):")
            for e in self.errors:
                print(e)
            print()
        else:
            print("ERRORS: none\n")

        if self.warnings:
            print(f"WARNINGS ({len(self.warnings)}):")
            for w in self.warnings:
                print(w)
            print()
        else:
            print("WARNINGS: none\n")

        if self.errors:
            print(f"✗  {len(self.errors)} structural error(s) found.")
            return 1
        else:
            suffix = f" (with {len(self.warnings)} warning(s))." if self.warnings else "."
            print(f"✓  No structural errors detected{suffix}")
            return 0


# ── Checks ─────────────────────────────────────────────────────────────────────

def check_root(root, r):
    """Dataset-level required and recommended files."""
    # Required
    if not (root / "dataset_description.json").exists():
        r.error("dataset_description.json is REQUIRED but missing")
    else:
        try:
            desc = json.loads((root / "dataset_description.json").read_text())
            if "Name" not in desc:
                r.error("dataset_description.json is missing required field: Name")
            if "BIDSVersion" not in desc:
                r.error("dataset_description.json is missing required field: BIDSVersion")
        except json.JSONDecodeError:
            r.error("dataset_description.json is not valid JSON")

    readme = any((root / f).exists() for f in ("README", "README.md", "README.rst"))
    if not readme:
        r.error("README (or README.md / README.rst) is REQUIRED but missing")

    # Recommended
    if not (root / "participants.tsv").exists():
        r.warn("participants.tsv is RECOMMENDED but missing")
    if not (root / "CHANGES").exists():
        r.warn("CHANGES is RECOMMENDED but missing")


def check_subject_dirs(root, r):
    """Subject and session directory naming."""
    subjects = []
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        name = entry.name
        if name.startswith("sub-"):
            if not SUB_RE.match(name):
                r.error(f"Invalid subject directory name: {name} (label must be alphanumeric)")
            else:
                subjects.append(entry)
        elif name in {"derivatives", "sourcedata", "code", "stimuli", ".git"}:
            pass  # known non-subject dirs
        elif not name.startswith("."):
            r.warn(f"Unexpected top-level directory: {name}")

    for sub_dir in subjects:
        children = [e for e in sorted(sub_dir.iterdir()) if e.is_dir()]
        has_sessions  = any(c.name.startswith("ses-") for c in children)
        has_datatypes = any(c.name in VALID_DATATYPES for c in children)

        if has_sessions and has_datatypes:
            r.warn(
                f"Mixed session and non-session layout inside {sub_dir.name}",
                sub_dir.name,
            )

        if has_sessions:
            for entry in children:
                if entry.name.startswith("ses-"):
                    if not SES_RE.match(entry.name):
                        r.error(
                            f"Invalid session directory name: {entry.name} "
                            f"(label must be alphanumeric)",
                            sub_dir.name,
                        )
                    else:
                        check_datatype_dirs(entry, r, f"{sub_dir.name}/{entry.name}")
                elif entry.name not in VALID_DATATYPES:
                    r.warn(f"Unexpected directory inside {sub_dir.name}: {entry.name}", sub_dir.name)
        else:
            # Session-less: datatype dirs are direct children of sub dir
            check_datatype_dirs(sub_dir, r, sub_dir.name)

    return subjects


def check_datatype_dirs(parent, r, rel_prefix):
    """Validate datatype dirs and files within a subject (or session) dir."""
    for entry in sorted(parent.iterdir()):
        if not entry.is_dir():
            continue
        dtype = entry.name
        if dtype not in VALID_DATATYPES:
            if not dtype.startswith("ses-"):
                r.warn(f"Unknown datatype directory: {dtype}", rel_prefix)
            continue
        check_files_in_datatype(entry, dtype, r, f"{rel_prefix}/{dtype}")


def check_files_in_datatype(datatype_dir, dtype, r, rel_prefix):
    """Check individual files within a datatype directory."""
    niftis = {}  # stem → Path (for companion-file checks)

    for fpath in sorted(datatype_dir.iterdir()):
        if fpath.is_dir():
            continue
        name = fpath.name

        # Identify NIfTI files for companion checks
        if name.endswith(".nii") or name.endswith(".nii.gz"):
            stem = name.replace(".nii.gz", "").replace(".nii", "")
            niftis[stem] = fpath

        # Only validate BIDS-named files (skip sidecars and tsv; they get checked below)
        if not name.endswith((".nii", ".nii.gz")):
            continue

        stem = name.replace(".nii.gz", "").replace(".nii", "")
        check_filename(stem, dtype, r, rel_prefix)

    # Companion file checks
    for stem, fpath in niftis.items():
        parsed = parse_filename(stem)
        if parsed is None:
            continue
        entities, suffix, _ = parsed

        # DWI: requires .bvec and .bval
        if suffix in DWI_SUFFIXES:
            for ext in (".bvec", ".bval"):
                companion = datatype_dir / (stem + ext)
                if not companion.exists():
                    r.error(f"DWI file is missing required companion {ext}: {stem}.nii.gz",
                            rel_prefix)

        # Every NIfTI should have a JSON sidecar
        json_sidecar = datatype_dir / (stem + ".json")
        if not json_sidecar.exists():
            r.warn(f"No JSON sidecar found for: {stem}.nii.gz", rel_prefix)
        else:
            check_sidecar(json_sidecar, suffix, stem, datatype_dir, r, rel_prefix)


def check_filename(stem, dtype, r, rel_prefix):
    """Validate entity ordering, label format, and suffix."""
    parsed = parse_filename(stem)
    if parsed is None:
        r.error(f"Filename cannot be parsed as BIDS: {stem}", rel_prefix)
        return

    entities, suffix, _ = parsed
    entity_keys = [k for k, _ in entities]
    entity_dict = {k: v for k, v in entities}

    # sub must be first
    if not entity_keys or entity_keys[0] != "sub":
        r.error(f"Filename must start with sub-<label>: {stem}", rel_prefix)

    # Label values must be alphanumeric
    for key, val in entities:
        if not LABEL_RE.match(val):
            r.error(
                f"Entity '{key}' has invalid label '{val}' (must be alphanumeric, "
                f"no hyphens/underscores): {stem}",
                rel_prefix,
            )

    # Entity ordering
    positions = [ENTITY_ORDER.get(k, 99) for k in entity_keys]
    for i in range(len(positions) - 1):
        if positions[i] > positions[i + 1]:
            r.error(
                f"Entities out of canonical order ({entity_keys[i]} before "
                f"{entity_keys[i+1]} violates spec): {stem}",
                rel_prefix,
            )

    # task required for certain suffixes
    if suffix in TASK_REQUIRED_SUFFIXES and "task" not in entity_dict:
        r.error(f"Suffix '{suffix}' requires a task entity: {stem}", rel_prefix)


def check_sidecar(json_path, suffix, stem, datatype_dir, r, rel_prefix):
    """Check required fields in JSON sidecars."""
    try:
        sidecar = json.loads(json_path.read_text())
    except json.JSONDecodeError:
        r.error(f"Sidecar is not valid JSON: {json_path.name}", rel_prefix)
        return

    rel = f"{rel_prefix}/{json_path.name}"

    # BOLD / func sidecars
    if suffix in FUNC_SUFFIXES and suffix != "sbref":
        if "RepetitionTime" not in sidecar:
            r.error("BOLD sidecar missing REQUIRED field: RepetitionTime", rel)
        if "TaskName" not in sidecar:
            r.error("BOLD sidecar missing REQUIRED field: TaskName", rel)

    # Field map sidecars
    if datatype_dir.name == "fmap":
        if "IntendedFor" not in sidecar:
            r.error("Field map sidecar missing REQUIRED field: IntendedFor", rel)
        else:
            intended = sidecar["IntendedFor"]
            if isinstance(intended, str):
                intended = [intended]
            subject_dir = datatype_dir.parent
            # If session layout, subject is one level up
            if subject_dir.name.startswith("ses-"):
                subject_dir = subject_dir.parent
            for target in intended:
                target_path = subject_dir / target
                if not target_path.exists():
                    r.warn(
                        f"IntendedFor path does not exist: {target}",
                        rel,
                    )


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <dataset-path>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    if not root.is_dir():
        print(f"Error: not a directory: {root}", file=sys.stderr)
        sys.exit(1)

    r = Report(str(root))

    check_root(root, r)
    subjects = check_subject_dirs(root, r)

    if not subjects:
        r.error("No sub-* directories found — is this a BIDS dataset root?")

    sys.exit(r.print_report())


if __name__ == "__main__":
    main()
