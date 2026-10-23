#!/usr/bin/env python3
"""OpenSpec inventory: small capabilities, near-duplicate requirements,
implementation-detail wording, and the test markers each requirement carries.

Reads ``openspec/specs/<capability>/spec.md`` (``### Requirement:`` and
``#### Scenario:`` headings) and, with ``--tests``, every
``@pytest.mark.<marker>("<capability>", "<requirement>")`` in the test tree, so a
proposed merge can say which markers move.
"""

from __future__ import annotations

import ast
import difflib
import re
from collections import Counter, defaultdict
from pathlib import Path

from _common import deco_name, emit, iter_py, parse, parser, table

REQ = re.compile(r"^### Requirement:\s*(.+?)\s*$", re.M)
SCEN = re.compile(r"^#### Scenario:\s*(.+?)\s*$", re.M)
WORD = re.compile(r"[a-z0-9_]+")
STOP = set("the a an of to and or in on is are be by for with as that this it its at from shall must when then "
           "not no each every any which".split())
# Python mechanics, private names, and test machinery in a requirement read as implementation.
IMPL = re.compile(r"(`_[a-z]\w*`|\bissubclass\b|\bisinstance\b|`__\w+__`|\bmonkeypatch|\bmock\b|\bprivate (attribute|method|helper)"
                  r"|\binternal (helper|cache|attribute)|\bthread ?pool\b|\bpickl)", re.I)


def capabilities(specs: Path) -> dict[str, list[dict]]:
    caps = {}
    for spec in sorted(specs.glob("*/spec.md")):
        text = spec.read_text(encoding="utf-8")
        heads = list(REQ.finditer(text))
        reqs = []
        for i, m in enumerate(heads):
            end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
            body = text[m.end():end]
            body = re.split(r"^## ", body, flags=re.M)[0]
            reqs.append({"name": m.group(1), "body": body, "scenarios": SCEN.findall(body),
                         "line": text[: m.start()].count("\n") + 1})
        caps[spec.parent.name] = reqs
    return caps



def spec_markers(tests: Path, marker: str) -> Counter:
    counts: Counter = Counter()
    for path in iter_py(tests):
        for node in ast.walk(parse(path)):
            if isinstance(node, ast.Call) and deco_name(node) == marker and len(node.args) >= 2:
                a, b = node.args[:2]
                if isinstance(a, ast.Constant) and isinstance(b, ast.Constant):
                    counts[(a.value, b.value)] += 1
    return counts


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("specs", type=Path, help="openspec/specs directory")
    p.add_argument("--tests", type=Path, help="test directory, for the marker map")
    p.add_argument("--marker", default="spec")
    p.add_argument("--small", type=int, default=2, help="capabilities with at most this many requirements")
    p.add_argument("--similarity", type=float, default=0.6, help="word-sequence similarity for a near-duplicate")
    p.add_argument("--title-similarity", type=float, default=0.8, help="requirement-title similarity that flags a pair")
    p.add_argument("--generic", type=lambda v: v.split(","), default=[],
                   help="comma-separated project tokens too common to group capabilities by")
    args = p.parse_args()

    caps = capabilities(args.specs)
    marks = spec_markers(args.tests, args.marker) if args.tests else Counter()
    n_req = sum(map(len, caps.values()))

    small = [(c, r) for c, r in caps.items() if len(r) <= args.small]

    flat = [(c, r) for c, rs in caps.items() for r in rs]
    words = [[w for w in WORD.findall((r["name"] + " " + r["body"]).lower()) if w not in STOP] for _, r in flat]
    bags = [set(w) for w in words]
    dups = []
    for i in range(len(flat)):
        for j in range(i + 1, len(flat)):
            if flat[i][0] == flat[j][0] or not bags[i] or not bags[j]:
                continue
            # Titles that differ by a substituted noun ("Edge summaries ..." / "Node
            # summaries ...") flag the pair even when the bodies have drifted apart.
            title = difflib.SequenceMatcher(None, flat[i][1]["name"].lower().split(),
                                            flat[j][1]["name"].lower().split()).ratio()
            if title < args.title_similarity and (
                len(bags[i] & bags[j]) / len(bags[i] | bags[j]) < args.similarity * 0.6
            ):
                continue  # cheap prefilter on the word sets
            # Sequence similarity tolerates a substituted noun (edge/node, delta/trend)
            # that breaks every n-gram it touches.
            ratio = difflib.SequenceMatcher(None, words[i], words[j], autojunk=False).ratio()
            if ratio >= args.similarity or title >= args.title_similarity:
                dups.append((round(ratio, 2), flat[i], flat[j]))
    dups.sort(key=lambda d: -d[0])

    impl = []
    for c, r in flat:
        for line in r["body"].splitlines():
            if IMPL.search(line):
                impl.append((c, r["name"], line.strip()[:140]))

    # Capabilities whose names share a non-generic token: fragmentation candidates.
    tokens = defaultdict(list)
    generic = {"features", "feature", "spec", "export", "api", "data", "and"} | set(args.generic)
    for c in caps:
        for t in c.split("-"):
            if t not in generic and len(t) > 3:
                tokens[t].append(c)
    families = {t: cs for t, cs in tokens.items() if len(cs) >= 2 and any(len(caps[x]) <= 3 for x in cs)}

    def marker_count(c, r):
        return marks.get((c, r["name"]), 0)

    md = ["# OpenSpec inventory", "",
          f"Method: {len(caps)} capabilities, {n_req} requirements parsed from `{args.specs}`; "
          f"{sum(marks.values())} `{args.marker}` markers read. Near-duplicates: word-sequence similarity "
          f">= {args.similarity} (stop words dropped), or title similarity >= {args.title_similarity}, "
          "across capabilities.", "",
          f"## Capabilities with <= {args.small} requirements: {len(small)}", ""]
    md.append(table(["capability", "requirements (markers)"],
                    [[c, "; ".join(f"{r['name']} ({marker_count(c, r)})" for r in rs)] for c, rs in small]))
    md += ["", f"## Name families with a small member: {len(families)}", ""]
    md.append(table(["token", "capabilities (requirements)"],
                    [[t, ", ".join(f"{c} ({len(caps[c])})" for c in cs)] for t, cs in sorted(families.items())]))
    md += ["", f"## Near-duplicate requirements: {len(dups)}", ""]
    md.append(table(["similarity", "A", "B", "markers A/B"],
                    [[j, f"{a[0]}: {a[1]['name']}", f"{b[0]}: {b[1]['name']}",
                      f"{marker_count(*a)}/{marker_count(*b)}"] for j, a, b in dups]))
    md += ["", f"## Implementation-detail wording: {len(impl)} lines", ""]
    md.append(table(["capability", "requirement", "line"], [[c, r, f"`{l}`"] for c, r, l in impl]))
    unmarked = [(c, r["name"]) for c, r in flat if args.tests and not marker_count(c, r)]
    if args.tests:
        md += ["", f"## Requirements with no marker: {len(unmarked)}", ""]
        md.append(table(["capability", "requirement"], [list(u) for u in unmarked]))
    emit(args, {"capabilities": {c: [r["name"] for r in rs] for c, rs in caps.items()},
                "small": [c for c, _ in small], "families": families,
                "duplicates": [{"similarity": j, "a": [a[0], a[1]["name"]], "b": [b[0], b[1]["name"]]} for j, a, b in dups],
                "implementation": impl, "unmarked": unmarked}, "\n".join(md))


if __name__ == "__main__":
    main()
