#!/usr/bin/env python3
"""Coverage-subset candidates: test A whose covered lines (or arcs) are a subset of
test B's, where A and B carry a common requirement marker.

Reads the ``.coverage`` SQLite database written by
``pytest --cov=<pkg> --cov-branch --cov-context=test``. Only the ``|run`` phase of
each context counts. Parametrized instances are merged into one test. A candidate is
**not** a finding: equal coverage is not equal assertions. Read both tests and report
the pair only if the weaker one asserts nothing the stronger one does not.
"""

from __future__ import annotations

import ast
import re
import sqlite3
from collections import defaultdict
from pathlib import Path

from _common import deco_name, emit, normalized_hash, parse, parser, table


def numbits_to_lines(blob: bytes) -> set[int]:
    return {i * 8 + j for i, byte in enumerate(blob) for j in range(8) if byte & (1 << j)}


def coverage_by_test(db: Path) -> dict[str, frozenset]:
    con = sqlite3.connect(db)
    contexts = {cid: name for cid, name in con.execute("select id, context from context")}
    files = {fid: path for fid, path in con.execute("select id, path from file")}
    cov: dict[str, set] = defaultdict(set)

    def test_of(cid: int) -> str | None:
        name = contexts.get(cid, "")
        if not name.endswith("|run"):
            return None
        return re.sub(r"\[.*\]$", "", name[: -len("|run")])

    for fid, cid, a, b in con.execute("select file_id, context_id, fromno, tono from arc"):
        t = test_of(cid)
        if t:
            cov[t].add((files[fid], a, b))
    for fid, cid, blob in con.execute("select file_id, context_id, numbits from line_bits"):
        t = test_of(cid)
        if t:
            cov[t] |= {(files[fid], n) for n in numbits_to_lines(blob)}
    return {t: frozenset(v) for t, v in cov.items() if v}


def markers(root: Path, nodeids: set[str], marker: str) -> dict[str, set[tuple]]:
    """Requirement markers per test nodeid, from function, class and module ``pytestmark``."""
    out: dict[str, set[tuple]] = {}
    by_file = defaultdict(set)
    for n in nodeids:
        by_file[n.split("::")[0]].add(n)

    def marks(decos) -> set[tuple]:
        found = set()
        for d in decos:
            if isinstance(d, ast.Call) and deco_name(d) == marker:
                found.add(tuple(a.value for a in d.args if isinstance(a, ast.Constant)))
        return found

    for fname, ids in by_file.items():
        path = root / fname
        if not path.exists():
            continue
        tree = parse(path)
        module = set()
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets):
                vals = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
                module |= marks(vals)

        def walk(body, prefix, inherited):
            for node in body:
                if isinstance(node, ast.ClassDef):
                    yield from walk(node.body, prefix + node.name + "::", inherited | marks(node.decorator_list))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    yield prefix + node.name, inherited | marks(node.decorator_list)

        for name, m in walk(tree.body, f"{fname}::", module):
            if name in ids:
                out[name] = m
    return out


ASSERT_CALL = re.compile(r"^(assert_\w+|raises|warns|approx|assert\w*)$")


def assertions(root: Path, nodeid: str) -> set[str] | None:
    """Normalised assertion statements of a test: ``assert``, ``pytest.raises``/``warns``
    blocks, and ``assert_*`` calls (``np.testing``). ``None`` if the test is not found."""
    fname, *parts = nodeid.split("::")
    path = root / fname
    if not path.exists():
        return None
    body = parse(path).body
    node = None
    for part in parts:
        node = next((n for n in body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.name == part), None)
        if node is None:
            return None
        body = node.body
    out = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Assert):
            out.add(normalized_hash(sub, scope=node))
        elif isinstance(sub, ast.withitem) and isinstance(sub.context_expr, ast.Call):
            if ASSERT_CALL.match(deco_name(sub.context_expr)):
                out.add(normalized_hash(sub.context_expr, scope=node))
        elif isinstance(sub, ast.Expr) and isinstance(sub.value, ast.Call) and ASSERT_CALL.match(deco_name(sub.value)):
            out.add(normalized_hash(sub.value, scope=node))
    return out


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("coverage", type=Path, help=".coverage database")
    p.add_argument("--root", type=Path, default=Path("."), help="directory test nodeids are relative to")
    p.add_argument("--marker", default="spec")
    p.add_argument("--min-covered", type=int, default=5, help="ignore tests covering fewer units")
    args = p.parse_args()

    cov = coverage_by_test(args.coverage)
    marks = markers(args.root, set(cov), args.marker)
    groups: dict[tuple, list[str]] = defaultdict(list)
    for t, ms in marks.items():
        for m in ms:
            groups[m].append(t)

    seen: set[tuple[str, str]] = set()
    cands = []
    for m, tests in groups.items():
        for a in tests:
            ca = cov[a]
            if len(ca) < args.min_covered:
                continue
            for b in tests:
                if a == b or (a, b) in seen:
                    continue
                cb = cov[b]
                if ca <= cb and (ca != cb or a < b):
                    seen.add((a, b))
                    cands.append({"weaker": a, "stronger": b, "marker": " / ".join(map(str, m)),
                                  "covered": len(ca), "of": len(cb), "equal": ca == cb})
    cache: dict[str, set[str] | None] = {}

    def asserts(t: str) -> set[str] | None:
        if t not in cache:
            cache[t] = assertions(args.root, t)
        return cache[t]

    for c in cands:
        wa, sa = asserts(c["weaker"]), asserts(c["stronger"])
        c["assert_subset"] = wa is not None and sa is not None and wa <= sa
        if c["equal"] and not c["assert_subset"] and wa is not None and sa is not None and sa <= wa:
            # Equal coverage was emitted in one direction only; the assertions decide which is weaker.
            c["weaker"], c["stronger"], c["assert_subset"] = c["stronger"], c["weaker"], True
    cands.sort(key=lambda c: (not c["assert_subset"], c["weaker"].split("::")[0], -c["covered"]))
    by_weaker = defaultdict(list)
    for c in cands:
        by_weaker[c["weaker"]].append(c)
    for cs in by_weaker.values():
        cs.sort(key=lambda c: not c["assert_subset"])
    n_marked = sum(1 for m in marks.values() if m)
    strong = {w: cs for w, cs in by_weaker.items() if cs[0]["assert_subset"]}

    md = ["# Coverage-subset candidates", "",
          f"Method: per-test {'arc' if any(len(next(iter(v))) == 3 for v in cov.values()) else 'line'} sets from "
          f"`{args.coverage}` ({len(cov)} tests with coverage, {n_marked} with a `{args.marker}` marker); "
          f"pairs sharing a marker where one set is a subset of the other. {len(cands)} pairs, "
          f"{len(by_weaker)} distinct weaker tests. Second filter: the weaker test's normalised "
          f"assertions are a subset of the stronger one's: {len(strong)} weaker tests.", "",
          "Each row is a candidate. Read both tests before reporting it.", "",
          f"## Coverage and assertion subset: {len(strong)}", ""]
    cols = ["weaker", "stronger (first of n)", "n", "marker", "covered", "equal?"]

    def rows(d):
        return [[w, cs[0]["stronger"], len(cs), cs[0]["marker"], f"{cs[0]['covered']}/{cs[0]['of']}",
                 "yes" if cs[0]["equal"] else ""] for w, cs in d.items()]

    md.append(table(cols, rows(strong)))
    rest = {w: cs for w, cs in by_weaker.items() if w not in strong}
    md += ["", f"## Coverage subset only (the weaker test asserts something else): {len(rest)}", ""]
    md.append(table(cols, rows(rest)))
    emit(args, {"tests": len(cov), "pairs": cands}, "\n".join(md))


if __name__ == "__main__":
    main()
