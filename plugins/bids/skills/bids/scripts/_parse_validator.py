#!/usr/bin/env python3
"""Parse bids-validator --json / --format json output from stdin and print a readable report.

Handles both 2.x and 1.x output formats.

Usage: bids-validator <path> --format json | python3 _parse_validator.py <dataset-path> [<validator-version>]

2.x format:
  {"issues": {"issues": [...], "codeMessages": {...}}, "summary": {..., "schemaVersion": "..."}}
  Each issue: {"code": "...", "severity": "error"|"warning", "location": "...", ...}

1.x format:
  {"issues": {"errors": [...], "warnings": [...]}, "summary": {...}}
  Each issue: {"key": "...", "reason": "...", "files": [{"relativePath": "..."}]}
"""

import json
import sys
from collections import defaultdict


def fmt_locations(locs, limit=5):
    lines = []
    for loc in locs[:limit]:
        lines.append(f"    {loc}")
    if len(locs) > limit:
        lines.append(f"    … and {len(locs) - limit} more")
    return lines


def parse_v2(data):
    """Parse 2.x output. Returns (errors, warnings) as lists of (code, description, locations)."""
    issues_block = data.get("issues", {})
    flat = issues_block.get("issues", [])
    code_messages = issues_block.get("codeMessages", {})

    grouped = defaultdict(lambda: {"severity": "", "description": "", "locations": []})
    for issue in flat:
        code = issue.get("code", "UNKNOWN")
        severity = issue.get("severity", "warning")
        location = issue.get("location", "")
        sub_code = issue.get("subCode", "")
        issue_message = issue.get("issueMessage", "")

        # Build a display key: code + subCode if present
        display_key = f"{code}.{sub_code}" if sub_code else code

        entry = grouped[display_key]
        entry["severity"] = severity
        if not entry["description"]:
            # Prefer codeMessages for base code (first line only); fall back to issueMessage first line
            base_msg = code_messages.get(code, "").strip().split("\n")[0].strip()
            fallback = issue_message.strip().split("\n")[0].strip()
            entry["description"] = base_msg or fallback
        if location:
            entry["locations"].append(location)

    errors = []
    warnings = []
    for key, entry in grouped.items():
        record = (key, entry["description"], entry["locations"])
        if entry["severity"] == "error":
            errors.append(record)
        else:
            warnings.append(record)

    return errors, warnings


def parse_v1(data):
    """Parse 1.x output. Returns (errors, warnings) as lists of (key, reason, locations)."""
    issues = data.get("issues", {})
    raw_errors = issues.get("errors", [])
    raw_warnings = issues.get("warnings", [])

    def convert(items):
        result = []
        for item in items:
            key = item.get("key", "UNKNOWN")
            reason = item.get("reason", "")
            files = item.get("files", [])
            locs = [f.get("relativePath") or f.get("name", "?") for f in files]
            result.append((key, reason, locs))
        return result

    return convert(raw_errors), convert(raw_warnings)


def detect_format(data):
    """Return '2x' or '1x' based on JSON structure."""
    issues = data.get("issues", {})
    if isinstance(issues.get("issues"), list):
        return "2x"
    if "errors" in issues or "warnings" in issues:
        return "1x"
    return "2x"  # default to 2.x for unknown structure


def main():
    dataset = sys.argv[1] if len(sys.argv) > 1 else "(unknown)"
    validator_version = sys.argv[2] if len(sys.argv) > 2 else ""

    raw = sys.stdin.read().strip()
    if not raw:
        print("Error: no output from bids-validator (empty response).")
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        print("Error: could not parse bids-validator output as JSON.")
        print("Raw output:")
        print(raw[:500])
        sys.exit(1)

    fmt = detect_format(data)
    if fmt == "2x":
        errors, warnings = parse_v2(data)
    elif fmt == "1x":
        errors, warnings = parse_v1(data)
    else:
        print(f"Error: unrecognized bids-validator JSON structure (top-level keys: {list(data.keys())}).")
        sys.exit(1)

    summary = data.get("summary", {})
    subjects = summary.get("subjects", [])
    sessions = summary.get("sessions", [])
    tasks = summary.get("tasks", [])
    total = summary.get("totalFiles", "?")
    schema_version = summary.get("schemaVersion", "")

    # Header
    header = f"BIDS Validation Report: {dataset}"
    print(header)
    print("=" * len(header))

    meta_parts = []
    if validator_version:
        meta_parts.append(f"validator {validator_version}")
    if schema_version:
        meta_parts.append(f"schema {schema_version}")
    if meta_parts:
        print("Validator: " + ", ".join(meta_parts))

    summary_parts = [f"{total} files", f"{len(subjects)} subject(s)"]
    if sessions:
        summary_parts.append(f"{len(sessions)} session(s)")
    if tasks:
        summary_parts.append("tasks: " + " ".join(tasks))
    print("Summary:   " + ", ".join(summary_parts))
    print()

    # Errors
    if errors:
        print(f"ERRORS ({len(errors)}):")
        for code, description, locs in errors:
            print(f"  [{code}] {description}")
            for line in fmt_locations(locs):
                print(line)
        print()
    else:
        print("ERRORS: none\n")

    # Warnings
    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for code, description, locs in warnings:
            print(f"  [{code}] {description}")
            for line in fmt_locations(locs):
                print(line)
        print()
    else:
        print("WARNINGS: none\n")

    # Verdict
    if errors:
        print(f"✗  Dataset is NOT valid — {len(errors)} error type(s) must be fixed.")
        sys.exit(1)
    else:
        suffix = f" (with {len(warnings)} warning type(s))." if warnings else "."
        print(f"✓  Dataset is valid{suffix}")
        sys.exit(0)


if __name__ == "__main__":
    main()
