#!/usr/bin/env python3
"""Near-duplicate tests: clusters that are candidates for one ``parametrize``d test.

Three kinds, each reported once with its clusters:

- **argument**: bodies equal once constants are erased (differ only in values);
- **accessor**: bodies equal once attribute and free names are also erased (differ
  in which method, property or function is exercised);
- **class pair**: two test classes in one file, at least half of whose methods match
  one-to-one, by name or by token similarity at the accessor level (a suite
  duplicated for a sibling type).

Fixture parameters are local names, so tests differing only in a fixture fall into
the first kind. Already-parametrized tests are included and marked.
"""

from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import difflib

from _common import deco_name, emit, iter_py, node_count, normalized_dump, normalized_hash, parse, parser, rel, strip_docstring, table


def tests_in(path: Path):
    def walk(body, cls):
        for node in body:
            if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                yield from walk(node.body, node)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                yield node, cls

    yield from walk(parse(path).body, None)


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("tests", type=Path)
    p.add_argument("--min-size", type=int, default=3, help="smallest function cluster reported")
    p.add_argument("--min-nodes", type=int, default=12, help="ignore bodies smaller than this")
    p.add_argument("--class-overlap", type=float, default=0.5,
                   help="matched methods / larger class size for a class pair")
    p.add_argument("--method-similarity", type=float, default=0.85,
                   help="token similarity at which two methods match (accessor level)")
    args = p.parse_args()

    files = [f for f in iter_py(args.tests) if f.name.startswith("test")]
    arg_groups: dict[str, list[dict]] = defaultdict(list)
    acc_groups: dict[str, list[dict]] = defaultdict(list)
    class_dumps: dict[tuple[str, int], list[tuple[str, list[str]]]] = {}
    class_names: dict[tuple[str, int], str] = {}
    n_tests = 0
    for path in files:
        for fn, cls in tests_in(path):
            n_tests += 1
            body = strip_docstring(fn.body)
            size = node_count(body)
            site = {"site": f"{rel(path)}:{fn.lineno}", "name": (cls.name + "." if cls else "") + fn.name,
                    "param": any(deco_name(d) == "parametrize" for d in fn.decorator_list)}
            acc = normalized_hash(body, constants=True, accessors=True, scope=fn)
            if cls is not None:
                key = (rel(path), cls.lineno)
                dump = normalized_dump(body, constants=True, accessors=True, scope=fn)
                class_dumps.setdefault(key, []).append((fn.name, dump.replace("(", " ").replace(")", " ").replace(",", " ").split()))
                class_names[key] = cls.name
            if size < args.min_nodes:
                continue
            arg_groups[normalized_hash(body, constants=True, scope=fn)].append(site)
            acc_groups[acc].append(site)

    arg_clusters = [v for v in arg_groups.values() if len(v) >= args.min_size]
    in_arg = {s["site"] for v in arg_clusters for s in v}
    acc_clusters = [v for v in acc_groups.values()
                    if len(v) >= args.min_size and not {s["site"] for s in v} <= in_arg]

    pairs = []
    keys = sorted(class_dumps)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if a[0] != b[0]:
                continue  # class pairs are compared within one file
            da, db = class_dumps[a], class_dumps[b]
            if min(len(da), len(db)) < 2:
                continue
            used: set[int] = set()
            shared = 0
            for name_x, x in da:
                best, best_j = 0.0, -1
                for j, (name_y, y) in enumerate(db):
                    if j in used:
                        continue
                    if name_x == name_y:  # the same test name in a sibling suite
                        best, best_j = 1.0, j
                        break
                    sm = difflib.SequenceMatcher(None, x, y, autojunk=False)
                    if sm.real_quick_ratio() < args.method_similarity or sm.quick_ratio() < args.method_similarity:
                        continue
                    r = sm.ratio()
                    if r > best:
                        best, best_j = r, j
                if best >= args.method_similarity:
                    used.add(best_j)
                    shared += 1
            if shared >= 2 and shared / max(len(da), len(db)) >= args.class_overlap:
                pairs.append({"a": f"{a[0]}:{a[1]} {class_names[a]}", "b": f"{b[0]}:{b[1]} {class_names[b]}",
                              "methods": f"{shared} of {len(da)}/{len(db)}"})

    def files_of(v):
        return sorted({s["site"].split(":")[0] for s in v})

    def rows(clusters):
        return [[len(v), ", ".join(files_of(v)),
                 "; ".join(f"`{s['name']}`{' (param)' if s['param'] else ''} {s['site'].split(':')[-1]}" for s in v)]
                for v in sorted(clusters, key=lambda v: -len(v))]

    md = [f"# Near-duplicate tests in `{rel(args.tests)}`", "",
          f"Method: normalised-AST hashing of {n_tests} test functions in {len(files)} files "
          f"(bodies >= {args.min_nodes} nodes; clusters >= {args.min_size}).", "",
          f"## Argument-only: {len(arg_clusters)} clusters, {sum(map(len, arg_clusters))} tests", ""]
    md.append(table(["n", "files", "tests (line)"], rows(arg_clusters)))
    md += ["", f"## Accessor-only: {len(acc_clusters)} clusters, {sum(map(len, acc_clusters))} tests", ""]
    md.append(table(["n", "files", "tests (line)"], rows(acc_clusters)))
    md += ["", f"## Class pairs: {len(pairs)}", ""]
    md.append(table(["shared methods", "class A", "class B"], [[p_["methods"], p_["a"], p_["b"]] for p_ in pairs]))
    emit(args, {"files": len(files), "tests": n_tests, "argument": arg_clusters, "accessor": acc_clusters,
                "class_pairs": pairs}, "\n".join(md))


if __name__ == "__main__":
    main()
