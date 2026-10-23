#!/usr/bin/env python3
"""Tests that assert an implementation detail: tests that import a ``_``-prefixed
name from the package, import from a private module, or read a private attribute.

A private attribute counts only if the package itself defines that name (a
``def _x``, a ``self._x =`` assignment, or a class-level ``_x``), so ``_replace`` on
a namedtuple or ``_meta`` on a third-party object is not reported. Each test is
marked *deliberate* when its docstring or the comment lines just above it say why
(a public route is missing, the guard is unreachable, internals are pinned on
purpose); otherwise it is *incidental*.
"""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path

from _common import deco_name, emit, is_private, iter_py, parse, parser, rel, table

RATIONALE = re.compile(
    r"\b(no public|not public|unreachable|internal|private|directly|white-?box|pins? the helper|"
    r"implementation detail|guard|cannot be reached|no route)\b", re.I)


def private_names(src: Path) -> set[str]:
    names: set[str] = set()
    for path in iter_py(src):
        for node in ast.walk(parse(path)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and is_private(node.name):
                names.add(node.name)
            elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and is_private(node.attr):
                names.add(node.attr)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names |= {t.id for t in targets if isinstance(t, ast.Name) and is_private(t.id)}
    return names


def module_has_marker(tree: ast.Module, marker: str) -> bool:
    """True when a top-level ``pytestmark`` assignment carries ``pytest.mark.<marker>``."""
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "pytestmark" for t in node.targets):
            vals = node.value.elts if isinstance(node.value, (ast.List, ast.Tuple)) else [node.value]
            if any(deco_name(v) == marker for v in vals):
                return True
    return False


def has_spec(fn: ast.AST, cls: ast.ClassDef | None, module_marked: bool, marker: str) -> bool:
    for node in (fn, cls):
        if node is not None and any(deco_name(d) == marker for d in node.decorator_list):
            return True
    return module_marked


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("tests", type=Path)
    p.add_argument("--src", type=Path, required=True, help="the package under test")
    p.add_argument("--package", help="import name of the package (default: --src directory name)")
    p.add_argument("--marker", default="spec", help="requirement marker name (pytest.mark.<marker>)")
    args = p.parse_args()

    pkg = args.package or args.src.name
    privates = private_names(args.src)
    per_file: dict[str, dict] = {}
    sites: list[dict] = []
    files = [f for f in iter_py(args.tests) if f.name.startswith(("test", "conftest"))]

    for path in files:
        tree = parse(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        module_marked = module_has_marker(tree, args.marker)
        imported_private: set[str] = set()
        import_rows = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == pkg:
                private_mod = any(is_private(part) for part in node.module.split("."))
                for alias in node.names:
                    if is_private(alias.name):
                        imported_private.add(alias.asname or alias.name)
                        import_rows.append((node.lineno, f"{node.module}.{alias.name}"))
                    elif private_mod:
                        import_rows.append((node.lineno, f"{node.module}.{alias.name} (private module)"))
        stats = {"tests": 0, "unmarked": 0, "deliberate": 0, "imports": len(import_rows)}

        def walk(body, cls):
            for node in body:
                if isinstance(node, ast.ClassDef):
                    yield from walk(node.body, node)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                    yield node, cls

        for fn, cls in walk(tree.body, None):
            hits = set()
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Name) and sub.id in imported_private:
                    hits.add(sub.id)
                elif (isinstance(sub, ast.Attribute) and sub.attr in privates
                      and not (isinstance(sub.value, ast.Name) and sub.value.id in {"self", "cls"})):
                    hits.add("." + sub.attr)
                elif isinstance(sub, ast.Constant) and isinstance(sub.value, str) and sub.value in privates:
                    hits.add(repr(sub.value))  # monkeypatch.setattr(obj, "_x", ...) and getattr
            if not hits:
                continue
            doc = (ast.get_docstring(fn) or "") + " " + (ast.get_docstring(cls) or "" if cls else "")
            above = " ".join(lines[max(0, fn.lineno - 4): fn.lineno - 1])
            deliberate = bool(RATIONALE.search(doc + " " + above))
            marked = has_spec(fn, cls, module_marked, args.marker)
            stats["tests"] += 1
            stats["unmarked"] += not marked
            stats["deliberate"] += deliberate
            sites.append({"site": f"{rel(path)}:{fn.lineno}", "test": (cls.name + "." if cls else "") + fn.name,
                          "uses": sorted(hits), "marked": marked, "deliberate": deliberate})
        if stats["tests"] or stats["imports"]:
            per_file[rel(path)] = stats

    total = sum(s["tests"] for s in per_file.values())
    md = [f"# Implementation-detail tests in `{rel(args.tests)}`", "",
          f"Method: AST scan of {len(files)} test files for private imports from `{pkg}` and reads of the "
          f"{len(privates)} private names `{pkg}` defines. {total} tests in {sum(1 for s in per_file.values() if s['tests'])} files.", "",
          "## Per file", ""]
    md.append(table(["file", "tests", "unmarked", "deliberate", "incidental", "private imports"],
                    [[f, s["tests"], s["unmarked"], s["deliberate"], s["tests"] - s["deliberate"], s["imports"]]
                     for f, s in sorted(per_file.items(), key=lambda kv: -kv[1]["tests"])]))
    for title, pick in (("Incidental and unmarked", lambda s: not s["deliberate"] and not s["marked"]),
                        ("Incidental, marked", lambda s: not s["deliberate"] and s["marked"]),
                        ("Deliberate", lambda s: s["deliberate"])):
        chosen = [s for s in sites if pick(s)]
        md += ["", f"## {title}: {len(chosen)}", ""]
        md.append(table(["site", "test", "private uses"],
                        [[s["site"], f"`{s['test']}`", ", ".join(f"`{u}`" for u in s["uses"])] for s in chosen]))
    emit(args, {"files": per_file, "sites": sites}, "\n".join(md))


if __name__ == "__main__":
    main()
