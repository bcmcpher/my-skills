#!/usr/bin/env python3
"""Error taxonomy: every ``raise`` grouped by the kind of check it makes.

Each raise is classified from its guarding condition and its message, in this order:
unsupported mode, wrong type, shape, missing state, choice, missing key, range, other.
The classification is a heuristic; the report lists every site so a reader can
correct it. A kind whose sites raise more than one exception type is the finding.
"""

from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from pathlib import Path

from _common import emit, iter_py, parse, parser, rel, table

KINDS = ["unsupported mode", "wrong type", "shape", "missing state", "choice", "missing key", "range", "other"]

MSG = {
    "unsupported mode": r"\b(not (yet )?(supported|implemented|available)|unsupported|only (for|with|on|in) |dense|sparse (network|parcellation)|requires? a (region|dense|sparse))",
    "wrong type": r"(must be an? [a-z_ ]*(instance|str|string|int|integer|float|bool|array|ndarray|mapping|dict|list|sequence|callable|path)\b|expected an? .* (instance|type)|got (an? )?(type|instance)|not a (str|string|path|mapping|callable))",
    "shape": r"\b(shape|ndim|dimension|dimensional|same length|length of|lengths? (do not|must)|must have \d|mismatch(ed)? (length|size)|columns? .* rows?)\b",
    "missing state": r"(call [`'\"]?[a-z_.]+\(?\)?[`'\"]? (first|before)|not (been )?(computed|loaded|built|run|set|fitted)|has no [a-z_ ]+; |run [`'\"]?[a-z_.]+|no .* (has|have) been|before calling|is empty)",
    "choice": r"(must be one of|one of \{|one of \[|expected one of|unknown|unrecognised|unrecognized|invalid (choice|value|option|mode|method|policy|kind)|not a valid|choose from|valid (options|values|choices) are)",
    "missing key": r"(not found|no such|does not exist|not present|missing|not in (the )?[a-z_ ]*(keys|channels|features|labels|names))",
    "range": r"(must be (positive|negative|non-negative|nonnegative|finite|>=?|<=?|greater|less|at least|at most|between|in \[|in \(|within|a fraction|whole|an integer >=|> 0|>= 0)|out of range|outside|exceeds?|too (large|small|many|few)|\[0, ?1\])",
}


def message_of(node: ast.Raise) -> str:
    exc = node.exc
    if isinstance(exc, ast.Call) and exc.args:
        arg = exc.args[0]
        parts = []
        for sub in ast.walk(arg):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                parts.append(sub.value)
        return " ".join(parts) or ast.unparse(arg)
    return ""


def exc_type(node: ast.Raise) -> str | None:
    exc = node.exc
    if exc is None:
        return None  # bare re-raise
    target = exc.func if isinstance(exc, ast.Call) else exc
    if isinstance(target, ast.Attribute):
        return target.attr
    if isinstance(target, ast.Name):
        return target.id
    return None


def guards(tree: ast.Module) -> dict[int, str]:
    """Map each raise (by id) to the source of the nearest enclosing ``if`` test."""
    out: dict[int, str] = {}

    def visit(node: ast.AST, test: str) -> None:
        for field, value in ast.iter_fields(node):
            children = value if isinstance(value, list) else [value]
            for child in children:
                if not isinstance(child, ast.AST):
                    continue
                t = test
                if isinstance(node, ast.If) and field == "body":
                    t = ast.unparse(node.test)
                elif isinstance(node, ast.If) and field == "orelse":
                    t = "not (" + ast.unparse(node.test) + ")"
                if isinstance(child, ast.Raise):
                    out[id(child)] = t
                visit(child, t)

    visit(tree, "")
    return out


def classify(test: str, msg: str, etype: str) -> str:
    text = msg.lower()
    for kind in ("unsupported mode",):
        if re.search(MSG[kind], text) or etype == "NotImplementedError":
            return kind
    if re.search(r"\bisinstance\(", test) or re.search(MSG["wrong type"], text):
        return "wrong type"
    if re.search(r"\.(shape|ndim)\b|\blen\(", test) or re.search(MSG["shape"], text):
        return "shape"
    if re.search(MSG["missing state"], text) or re.search(r"\bself\.\w+ is None\b", test):
        return "missing state"
    if re.search(MSG["choice"], text) or re.search(r"not in \(|not in \{|not in \[|not in [A-Z_]{3,}", test):
        return "choice"
    if re.search(MSG["missing key"], text) or etype == "KeyError":
        return "missing key"
    if re.search(MSG["range"], text) or re.search(r"[<>]=?\s*-?\d|\d\s*[<>]=?", test):
        return "range"
    return "other"


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    args = p.parse_args()

    sites: dict[str, list[dict]] = defaultdict(list)
    total = 0
    for path in iter_py(args.root):
        tree = parse(path)
        g = guards(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Raise):
                continue
            etype = exc_type(node)
            if etype is None:
                continue
            total += 1
            msg = message_of(node)
            kind = classify(g.get(id(node), ""), msg, etype)
            sites[kind].append({"site": f"{rel(path)}:{node.lineno}", "type": etype, "message": msg[:120],
                                "guard": g.get(id(node), "")[:100]})

    summary = []
    for kind in KINDS:
        types = Counter(s["type"] for s in sites.get(kind, []))
        summary.append({"kind": kind, "sites": sum(types.values()), "types": dict(types.most_common())})
    mixed = [s for s in summary if len(s["types"]) > 1 and s["kind"] != "other"]

    md = [f"# Error taxonomy in `{rel(args.root)}`", "",
          f"Method: {total} `raise` sites with an exception (bare re-raises excluded), classified "
          "by guarding condition and message. Heuristic: check the site lists.", "",
          "## Per kind", ""]
    md.append(table(["kind", "sites", "types"],
                    [[s["kind"], s["sites"], ", ".join(f"{t} {n}" for t, n in s["types"].items())] for s in summary]))
    for s in mixed:
        md += ["", f"## Mixed: {s['kind']}", ""]
        rows = sorted(sites[s["kind"]], key=lambda r: (r["type"], r["site"]))
        md.append(table(["type", "site", "message", "guard"],
                        [[r["type"], r["site"], r["message"], f"`{r['guard']}`" if r["guard"] else ""] for r in rows]))
    emit(args, {"total": total, "summary": summary, "sites": sites}, "\n".join(md))


if __name__ == "__main__":
    main()
