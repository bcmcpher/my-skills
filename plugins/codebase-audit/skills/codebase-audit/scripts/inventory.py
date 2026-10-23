#!/usr/bin/env python3
"""Module sizes, and an outline of each large module for choosing split points.

The outline lists every top-level definition and every method of a large class with
its line range, plus comment banners (``# --- Title ---`` style section markers), so a
reader can name split points by line range rather than by impression.
"""

from __future__ import annotations

import re
from pathlib import Path

from _common import emit, iter_defs, iter_py, parser, rel, table

BANNER = re.compile(r"^\s*#\s*[-=#*~]{3,}\s*(?P<title>[^-=#*~].*?)?\s*[-=#*~]*\s*$")


def banners(path: Path) -> list[tuple[int, str]]:
    out = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines, 1):
        m = BANNER.match(line)
        if not m:
            continue
        title = (m.group("title") or "").strip()
        if not title and i < len(lines):  # banner line, title on the next comment line
            nxt = lines[i].strip()
            if nxt.startswith("#") and not BANNER.match(lines[i]):
                title = nxt.lstrip("# ").strip()
        if title:
            out.append((i, title))
    return out


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("root", type=Path, help="package or test directory")
    p.add_argument("--outline-min", type=int, default=1500, help="outline modules this long")
    p.add_argument("--class-min", type=int, default=300, help="list methods of classes this long")
    args = p.parse_args()

    modules = []
    for path in iter_py(args.root):
        n = len(path.read_text(encoding="utf-8").splitlines())
        modules.append({"module": rel(path), "lines": n})
    modules.sort(key=lambda m: -m["lines"])

    outlines = {}
    for m in modules:
        if m["lines"] < args.outline_min:
            continue
        path = Path(m["module"])
        items = []
        for d in iter_defs(path):
            start, end = d.span
            size = end - start + 1
            top = d.parent is None
            big_parent = d.parent is not None and (
                (d.parent.end_lineno or 0) - d.parent.lineno + 1 >= args.class_min
            )
            nested_class_member = d.parent is not None and "." in d.qualname.rsplit(".", 1)[0]
            if top or (big_parent and not nested_class_member):
                items.append(
                    {"name": d.qualname, "kind": d.kind, "start": start, "end": end, "lines": size}
                )
        for line, title in banners(path):
            items.append({"name": f"# {title}", "kind": "banner", "start": line, "end": line, "lines": 0})
        items.sort(key=lambda i: i["start"])
        outlines[m["module"]] = items

    md = [f"# Inventory of `{rel(args.root)}`", "", f"{len(modules)} modules, "
          f"{sum(m['lines'] for m in modules)} lines.", ""]
    md.append(table(["module", "lines"], [[m["module"], m["lines"]] for m in modules[:40]]))
    for mod, items in outlines.items():
        md += ["", f"## Outline: `{mod}`", ""]
        md.append(table(["lines", "size", "kind", "name"],
                        [[f"{i['start']}-{i['end']}", i["lines"] or "", i["kind"], i["name"]]
                         for i in items]))
    emit(args, {"modules": modules, "outlines": outlines}, "\n".join(md))


if __name__ == "__main__":
    main()
