#!/usr/bin/env python3
"""Duplicated logic: identical function bodies, repeated statement blocks, and
repeated optional-dependency guards.

Bodies and blocks are compared after normalisation: local names are renamed
canonically, free names (the helpers and builtins being called) are kept. Private
functions are included: copied helpers are usually private. A block cluster that
includes a site inside ``--helpers`` is flagged: code elsewhere re-implements a
shared helper instead of calling it.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from _common import emit, iter_defs, iter_py, node_count, normalized_hash, parse, parser, rel, strip_docstring, table


def function_sites(paths: list[Path], min_nodes: int, constants: bool = False) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for path in paths:
        for d in iter_defs(path):
            if isinstance(d.node, ast.ClassDef):
                continue
            body = strip_docstring(d.node.body)
            if node_count(body) < min_nodes:
                continue
            key = normalized_hash(body, scope=d.node, constants=constants)
            groups[key].append({"site": d.loc(), "name": d.qualname, "nodes": node_count(body)})
    return {k: v for k, v in groups.items() if len(v) > 1}


def _bodies(tree: ast.AST):
    """Every statement list in the tree, with its enclosing function (or None)."""

    def visit(node: ast.AST, scope: ast.AST | None):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scope = node
        for field in ("body", "orelse", "finalbody"):
            stmts = getattr(node, field, None)
            if isinstance(stmts, list) and stmts and isinstance(stmts[0], ast.stmt):
                yield stmts, scope
        for h in getattr(node, "handlers", []) or []:
            yield h.body, scope
        for child in ast.iter_child_nodes(node):
            yield from visit(child, scope)

    yield from visit(tree, None)


def block_sites(paths: list[Path], window: int, min_nodes: int, constants: bool = False) -> dict[str, list[dict]]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for path in paths:
        for stmts, scope in _bodies(parse(path)):
            stmts = strip_docstring(stmts)
            for i in range(len(stmts) - window + 1):
                block = stmts[i : i + window]
                if any(isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom)) for s in block):
                    continue
                if scope is None or all(isinstance(s, ast.AnnAssign) and s.value is None for s in block):
                    continue  # class-field declarations and module setup are not logic
                n = node_count(block)
                if n < min_nodes:
                    continue
                key = normalized_hash(block, scope=scope, constants=constants)
                fn = getattr(scope, "name", "<module>")
                groups[key].append({"site": f"{rel(path)}:{block[0].lineno}", "function": fn, "nodes": n,
                                    "first": ast.unparse(block[0]).splitlines()[0][:90]})
    out = {}
    for k, v in groups.items():
        # One site per function: overlapping windows of a self-similar run are one site.
        per_fn: dict[tuple[str, str], dict] = {}
        for site in v:
            per_fn.setdefault((site["site"].split(":")[0], site["function"]), site)
        if len(per_fn) > 1:  # a cluster must span more than one function
            out[k] = list(per_fn.values())
    return out


def _collapse_overlaps(clusters: dict[str, list[dict]], window: int) -> list[list[dict]]:
    """Adjacent windows of one long repeated run produce one cluster per offset; keep
    the first window of each run."""
    seen: set[tuple[str, ...]] = set()
    out = []
    for sites in sorted(clusters.values(), key=lambda v: [s["site"] for s in v]):
        sig = []
        for s in sites:
            f, line = s["site"].rsplit(":", 1)
            sig.append((f, int(line)))
        key = tuple(sorted(f"{f}:{line}" for f, line in sig))
        near = any(
            all(any(f2 == f and 0 < line - l2 <= window * 8 for f2, l2 in prev) for f, line in sig)
            for prev in [tuple((p.rsplit(":", 1)[0], int(p.rsplit(":", 1)[1])) for p in k) for k in seen]
        )
        seen.add(key)
        if not near:
            out.append(sites)
    return out


def optional_guards(paths: list[Path]) -> dict[str, list[str]]:
    """``try: import X`` / ``except ImportError`` sites, grouped by module X."""
    groups: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        for node in ast.walk(parse(path)):
            if not isinstance(node, ast.Try):
                continue
            catches = {ast.unparse(h.type) if h.type else "" for h in node.handlers}
            if not any("ImportError" in c or "ModuleNotFoundError" in c for c in catches):
                continue
            for stmt in node.body:
                for sub in ast.walk(stmt):
                    if isinstance(sub, ast.Import):
                        mods = [a.name.split(".")[0] for a in sub.names]
                    elif isinstance(sub, ast.ImportFrom) and sub.module and sub.level == 0:
                        mods = [sub.module.split(".")[0]]
                    else:
                        continue
                    for m in mods:
                        groups[m].append(f"{rel(path)}:{node.lineno}")
    return {k: sorted(set(v)) for k, v in groups.items()}


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    p.add_argument("--helpers", type=Path, action="append", default=[],
                   help="shared-helper module or package (repeatable)")
    p.add_argument("--min-nodes", type=int, default=25, help="ignore bodies smaller than this")
    p.add_argument("--window", type=int, default=3, help="statements per block")
    p.add_argument("--block-min-nodes", type=int, default=30)
    args = p.parse_args()

    paths = iter_py(args.root)
    helper_prefixes = [rel(h) for h in args.helpers]

    funcs = function_sites(paths, args.min_nodes)
    exact_sites = {s["site"] for v in funcs.values() for s in v}
    shaped = {k: v for k, v in function_sites(paths, args.min_nodes, constants=True).items()
              if not {s["site"] for s in v} <= exact_sites}
    blocks = _collapse_overlaps(block_sites(paths, args.window, args.block_min_nodes), args.window)
    guards = optional_guards(paths)

    def touches_helper(sites: list[dict]) -> bool:
        return any(s["site"].startswith(tuple(helper_prefixes)) for s in sites) if helper_prefixes else False

    func_rows = sorted(funcs.values(), key=lambda v: (-len(v), -v[0]["nodes"]))
    block_rows = sorted(blocks, key=lambda v: (not touches_helper(v), -len(v), -v[0]["nodes"]))

    md = [f"# Duplicated logic in `{rel(args.root)}`", "",
          f"Method: normalised-AST hashing of {len(paths)} modules. Function bodies >= "
          f"{args.min_nodes} nodes (public and private); {args.window}-statement blocks >= "
          f"{args.block_min_nodes} nodes spanning more than one function; try/except ImportError guards.", "",
          f"## Identical function bodies: {len(func_rows)} clusters", ""]
    md.append(table(["n", "nodes", "sites"],
                    [[len(v), v[0]["nodes"], "; ".join(f"`{s['name']}` {s['site']}" for s in v)] for v in func_rows]))
    shaped_rows = sorted(shaped.values(), key=lambda v: (-len(v), -v[0]["nodes"]))
    md += ["", f"## Same-shape function bodies (differ only in constants): {len(shaped_rows)} clusters", ""]
    md.append(table(["n", "nodes", "sites"],
                    [[len(v), v[0]["nodes"], "; ".join(f"`{s['name']}` {s['site']}" for s in v)] for v in shaped_rows]))
    md += ["", f"## Repeated statement blocks: {len(block_rows)} clusters", ""]
    md.append(table(["n", "helper?", "nodes", "first statement", "sites"],
                    [[len(v), "yes" if touches_helper(v) else "", v[0]["nodes"], f"`{v[0]['first']}`",
                      "; ".join(f"{s['site']} ({s['function']})" for s in v)] for v in block_rows]))
    md += ["", f"## Optional-dependency guards: {len(guards)} modules", ""]
    md.append(table(["module", "n", "sites"], [[m, len(s), "; ".join(s)] for m, s in sorted(guards.items(), key=lambda kv: -len(kv[1]))]))
    emit(args, {"functions": func_rows, "shaped": shaped_rows, "blocks": block_rows, "guards": guards,
                "modules": len(paths)}, "\n".join(md))


if __name__ == "__main__":
    main()
