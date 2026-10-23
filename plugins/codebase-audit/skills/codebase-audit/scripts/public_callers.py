#!/usr/bin/env python3
"""Public API with no caller outside the tests.

A public definition is a function, class, method or property whose qualified name
has no ``_``-prefixed part. A *use* is any reference to its name: a ``Name``, an
attribute access, an import, an ``__all__`` entry, or a string constant equal to the
name (``getattr`` dispatch and registries). Uses in the definition's own body do not
count, so recursion and a delegating wrapper do not count for themselves. The match is by name, not by type, so a common name used elsewhere hides a
dead definition: the report errs towards false negatives, never false positives.
"""

from __future__ import annotations

import ast
import re
from fnmatch import fnmatch
from collections import defaultdict
from pathlib import Path

from _common import emit, iter_defs, iter_py, parse, parser, rel, table

WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def use_sites(paths: list[Path]) -> dict[str, list[tuple[Path, int]]]:
    """Every use of every name, with where it occurs."""
    sites: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for path in paths:
        if path.suffix != ".py":
            for name in WORD.findall(path.read_text(encoding="utf-8", errors="replace")):
                sites[name].append((path, 0))
            continue
        for node in ast.walk(parse(path)):
            name = None
            if isinstance(node, ast.Name):
                name = node.id
            elif isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.alias):
                name = (node.asname or node.name).split(".")[-1]
                sites[node.name.split(".")[-1]].append((path, node.lineno))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and WORD.fullmatch(node.value):
                name = node.value
            if name is not None:
                sites[name].append((path, getattr(node, "lineno", 0)))
    return sites


def uses_of(d, sites: dict[str, list[tuple[Path, int]]]) -> int:
    """Uses of ``d``'s name outside ``d``'s own body. Excluding only its own span keeps
    ``self.other.name()`` inside a same-named method as a use of the other definition,
    while recursion and a delegating wrapper do not count for themselves."""
    start, end = d.span
    return sum(1 for path, line in sites.get(d.name, []) if not (path == d.path and start <= line <= end))


def exported(src: Path) -> set[str]:
    names: set[str] = set()
    for init in src.rglob("__init__.py"):
        for node in ast.walk(parse(init)):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__all__" for t in node.targets):
                if isinstance(node.value, (ast.List, ast.Tuple)):
                    names |= {e.value for e in node.value.elts if isinstance(e, ast.Constant)}
    return names


def docstring_stance(d) -> str:
    doc = ast.get_docstring(d.node) or ""
    if not doc:
        return "undocumented"
    if re.search(r"^\s*Examples?\s*\n\s*-{3,}", doc, re.M) or ">>>" in doc:
        return "user API (has examples)"
    if re.search(r"\b(internal|private|helper|for tests?|testing only)\b", doc, re.I):
        return "internal (docstring says so)"
    return "documented"


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("src", type=Path, help="package directory")
    p.add_argument("--tests", type=Path, action="append", default=[], help="test directory (repeatable)")
    p.add_argument("--extra", type=Path, action="append", default=[],
                   help="other non-test callers: examples, scripts, docs (repeatable)")
    p.add_argument("--exclude", action="append", default=[],
                   help="file-name glob to drop from --extra (repeatable); audit records and plans name "
                        "the very definitions under audit, so they must not count as callers")
    args = p.parse_args()

    src_paths = iter_py(args.src)
    defs = [d for path in src_paths for d in iter_defs(path) if d.public]
    # __init__ re-exports are bookkeeping, not callers.
    non_init = [p for p in src_paths if p.name != "__init__.py"]
    src_sites = use_sites(non_init)
    extra_paths = [f for e in args.extra for f in ([e] if e.is_file() else sorted(x for x in e.rglob("*") if x.is_file() and x.suffix in {".py", ".md", ".ipynb", ".rst", ".txt"}))]
    extra_paths = [f for f in extra_paths if not any(fnmatch(f.name, g) for g in args.exclude)]
    extra_sites = use_sites(extra_paths)
    test_sites = use_sites([f for t in args.tests for f in iter_py(t)])
    exports = exported(args.src)

    rows = []
    for d in defs:
        if d.name in {"main"}:
            continue
        if uses_of(d, src_sites) or extra_sites.get(d.name):
            continue
        rows.append({
            "name": d.qualname, "kind": d.kind, "site": d.loc(), "exported": d.name in exports,
            "test_refs": len(test_sites.get(d.name, [])), "docstring": docstring_stance(d),
        })
    test_only = [r for r in rows if r["test_refs"]]
    unused = [r for r in rows if not r["test_refs"]]

    md = [f"# Public API without a non-test caller in `{rel(args.src)}`", "",
          f"Method: name-level reference count over {len(src_paths)} source modules "
          f"(excluding `__init__` re-exports and each definition's own body), "
          f"{len(extra_paths)} extra files, and the tests. {len(defs)} public definitions examined.", "",
          f"## Test-only callers: {len(test_only)}", ""]
    cols = ["name", "kind", "site", "exported", "test refs", "docstring"]
    md.append(table(cols, [[f"`{r['name']}`", r["kind"], r["site"], "yes" if r["exported"] else "",
                            r["test_refs"], r["docstring"]] for r in test_only]))
    md += ["", f"## No caller at all: {len(unused)}", ""]
    md.append(table(cols, [[f"`{r['name']}`", r["kind"], r["site"], "yes" if r["exported"] else "",
                            0, r["docstring"]] for r in unused]))
    emit(args, {"examined": len(defs), "test_only": test_only, "unused": unused}, "\n".join(md))


if __name__ == "__main__":
    main()
