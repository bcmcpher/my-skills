#!/usr/bin/env python3
"""Docstrings against signatures: numpydoc ``Parameters`` sections compared with
the function's arguments, defaults and ``Literal[...]`` annotations.

Checks, per function with a ``Parameters`` section:

- documented name absent from the signature (and no ``**kwargs``);
- signature argument not documented;
- documented default that differs from the signature default;
- documented value (quoted in the type line, or quoted in the description beside a
  value that *is* allowed) that the ``Literal`` annotation does not accept;
- ``Literal`` value that the docstring never mentions.

``Literal`` aliases (``X = Literal[...]``, ``type X = Literal[...]``) are resolved
across the whole tree by name.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from _common import emit, iter_defs, iter_py, parse, parser, table

SECTION = re.compile(r"^(?P<indent>\s*)(?P<title>[A-Z][A-Za-z ]+)\n(?P=indent)-{3,}\s*$", re.M)
PARAM = re.compile(
    r"^(?P<names>\*{0,2}[A-Za-z_]\w*(?:\s*,\s*\*{0,2}[A-Za-z_]\w*)*)(?:\s+:\s+(?P<type>.*)|\s*:\s*)?$"
)
QUOTED = re.compile(r"""(?<![\w])["'`]{1,2}([^"'`\s][^"'`]{0,40}?)["'`]{1,2}(?![\w])""")
DEFAULT = re.compile(
    r"\bdefaults?(?: is| to|:|=)?\s+(?P<v>[`\"'][^`\"']+[`\"']|-?\d[\d.e_-]*|True|False|None)(?![\w])", re.I
)


def literal_values(node: ast.expr | None, aliases: dict[str, set]) -> set | None:
    """Values accepted by an annotation, if it is built only from Literals and None."""
    if node is None:
        return None
    vals: set = set()
    ok = False
    for sub in _union_members(node):
        if isinstance(sub, ast.Subscript) and _name(sub.value) == "Literal":
            elts = sub.slice.elts if isinstance(sub.slice, ast.Tuple) else [sub.slice]
            vals |= {e.value for e in elts if isinstance(e, ast.Constant)}
            ok = True
        elif _name(sub) in aliases:
            vals |= aliases[_name(sub)]
            ok = True
        elif isinstance(sub, ast.Constant) and sub.value is None:
            continue
        else:
            return None  # a non-literal member: the type accepts arbitrary values
    return vals if ok else None


def _union_members(node: ast.expr) -> list[ast.expr]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return _union_members(node.left) + _union_members(node.right)
    if isinstance(node, ast.Subscript) and _name(node.value) in {"Optional", "Union"}:
        elts = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
        return [m for e in elts for m in _union_members(e)]
    return [node]


def _name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def collect_aliases(paths: list[Path]) -> dict[str, set]:
    aliases: dict[str, set] = {}
    for _ in range(3):  # aliases of aliases
        for path in paths:
            for node in parse(path).body:
                target, value = None, None
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    target, value = node.targets[0].id, node.value
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                    target, value = node.target.id, node.value
                elif hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
                    target, value = node.name.id, node.value
                if target and value is not None:
                    vals = literal_values(value, aliases)
                    if vals:
                        aliases[target] = vals
    return aliases


def parse_params(doc: str) -> dict[str, dict]:
    sections = list(SECTION.finditer(doc))
    out: dict[str, dict] = {}
    for i, m in enumerate(sections):
        if m.group("title").strip() not in {"Parameters", "Other Parameters", "Keyword Arguments"}:
            continue
        end = sections[i + 1].start() if i + 1 < len(sections) else len(doc)
        block = doc[m.end():end].splitlines()
        base = None
        current = None
        for line in block:
            if not line.strip():
                if current:
                    out[current]["desc"] += "\n"
                continue
            indent = len(line) - len(line.lstrip())
            if base is None:
                base = indent
            if indent == base:
                pm = PARAM.match(line.strip())
                if not pm:
                    current = None
                    continue
                names = [n.strip().lstrip("*") for n in pm.group("names").split(",")]
                for n in names:
                    out[n] = {"type": pm.group("type") or "", "desc": ""}
                current = names[-1]
                for n in names[:-1]:
                    out[n] = out[current] = out[n] | {"shared": True}
            elif current:
                out[current]["desc"] += line.strip() + " "
    return out


def signature(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[dict[str, dict], bool]:
    a = fn.args
    positional = a.posonlyargs + a.args
    defaults: list[ast.expr | None] = [None] * (len(positional) - len(a.defaults)) + list(a.defaults)
    params = {}
    for arg, default in zip(positional, defaults):
        params[arg.arg] = {"annotation": arg.annotation, "default": default}
    for arg, default in zip(a.kwonlyargs, a.kw_defaults):
        params[arg.arg] = {"annotation": arg.annotation, "default": default}
    if a.vararg:
        params[a.vararg.arg] = {"annotation": None, "default": None}
    for skip in ("self", "cls"):
        params.pop(skip, None)
    return params, a.kwarg is not None


def _norm(v: str) -> str:
    return v.strip("`'\". ").replace("'", '"')


def main() -> None:
    p = parser(__doc__.splitlines()[0])
    p.add_argument("root", type=Path)
    p.add_argument("--include-private", action="store_true")
    args = p.parse_args()

    paths = iter_py(args.root)
    aliases = collect_aliases(paths)
    checked = {"public": 0, "private": 0, "class": 0}
    issues: list[dict] = []
    undocumented: list[dict] = []

    for path in paths:
        for d in iter_defs(path):
            if isinstance(d.node, ast.ClassDef):
                doc = ast.get_docstring(d.node) or ""
                has_init = any(isinstance(n, ast.FunctionDef) and n.name == "__init__" for n in d.node.body)
                if "Parameters" in doc and not has_init and (documented := parse_params(doc)):
                    checked["class"] += 1
                    fields = {n.target.id for n in d.node.body
                              if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}
                    for name in documented:
                        if fields and name not in fields:
                            issues.append({"site": d.loc(), "function": d.qualname, "param": name,
                                           "check": "documented, not a field", "detail": ""})
                continue
            doc = ast.get_docstring(d.node) or ""
            fn = d.node
            if "Parameters" not in doc and d.name == "__init__" and d.parent is not None:
                doc = ast.get_docstring(d.parent) or ""  # numpydoc: class docstring documents __init__
            if "Parameters" not in doc:
                continue
            documented = parse_params(doc)
            if not documented:
                continue
            checked["public" if d.public else "private"] += 1
            if not d.public and not args.include_private:
                continue
            sig, has_kwargs = signature(fn)
            loc = d.loc()

            for name in documented:
                if name not in sig and not has_kwargs:
                    issues.append({"site": loc, "function": d.qualname, "param": name, "check": "documented, not in signature", "detail": ""})
            for name in sig:
                if name not in documented:
                    undocumented.append({"site": loc, "function": d.qualname, "param": name})

            for name, info in documented.items():
                if name not in sig:
                    continue
                ann, default = sig[name]["annotation"], sig[name]["default"]
                text = info["type"] + " " + info["desc"]
                dm = DEFAULT.search(text)
                if dm and default is not None:
                    doc_default = _norm(dm.group("v"))
                    sig_default = _norm(ast.unparse(default))
                    if doc_default and doc_default != sig_default and doc_default.lower() not in {"value", "the", "a", "an", "none" if sig_default != "None" else "~"}:
                        issues.append({"site": loc, "function": d.qualname, "param": name, "check": "default differs",
                                       "detail": f"doc {doc_default!r}, signature {sig_default!r}"})
                allowed = literal_values(ann, aliases)
                if not allowed:
                    continue
                str_allowed = {v for v in allowed if isinstance(v, str)}
                type_quoted = set(QUOTED.findall(info["type"]))
                desc_quoted = set(QUOTED.findall(info["desc"]))
                suspicious = {v for v in type_quoted if v not in str_allowed}
                if desc_quoted & str_allowed:  # the description is enumerating values
                    suspicious |= {v for v in desc_quoted if v not in str_allowed and v.isidentifier() and v != name}
                if suspicious:
                    issues.append({"site": loc, "function": d.qualname, "param": name, "check": "documented value not accepted",
                                   "detail": f"doc {sorted(suspicious)}; Literal {sorted(map(str, allowed))}"})
                missing = {v for v in str_allowed if v not in text}
                if missing and (type_quoted or desc_quoted & str_allowed):
                    issues.append({"site": loc, "function": d.qualname, "param": name, "check": "accepted value not documented",
                                   "detail": f"{sorted(missing)}"})

    md = ["# Docstrings against signatures", "",
          f"Method: numpydoc `Parameters` parsed with regex, signatures and `Literal` annotations "
          f"from the AST ({len(aliases)} Literal aliases resolved). Functions with a `Parameters` "
          f"section: {checked['public']} public, {checked['private']} private; "
          f"{checked['class']} classes without `__init__` checked against their fields"
          f"{' (all checked)' if args.include_private else ' (public checked)'}.", "",
          f"## Disagreements: {len(issues)}", ""]
    md.append(table(["site", "function", "param", "check", "detail"],
                    [[i["site"], f"`{i['function']}`", f"`{i['param']}`", i["check"], i["detail"]] for i in issues]))
    md += ["", f"## Signature arguments not documented: {len(undocumented)}", ""]
    md.append(table(["site", "function", "param"], [[u["site"], f"`{u['function']}`", f"`{u['param']}`"] for u in undocumented]))
    emit(args, {"checked": checked, "issues": issues, "undocumented": undocumented}, "\n".join(md))


if __name__ == "__main__":
    main()
