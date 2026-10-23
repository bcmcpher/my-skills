"""Shared helpers for the codebase-audit sweep scripts.

Every script walks a tree of Python files with ``ast`` only, never imports the code
under audit, and prints either a markdown report (default) or JSON (``--json``).
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

SKIP_DIRS = {"__pycache__", ".git", ".venv", "build", "dist", ".tox", ".mypy_cache"}


def iter_py(root: Path) -> list[Path]:
    """Every ``.py`` file under ``root`` (or ``root`` itself), sorted."""
    if root.is_file():
        return [root]
    return sorted(
        p for p in root.rglob("*.py") if not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )


@lru_cache(maxsize=None)
def parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def rel(path: Path, base: Path | None = None) -> str:
    base = base or Path.cwd()
    try:
        return str(path.resolve().relative_to(base.resolve()))
    except ValueError:
        return str(path)


def is_private(name: str) -> bool:
    return name.startswith("_") and not is_dunder(name)


def is_dunder(name: str) -> bool:
    return name.startswith("__") and name.endswith("__") and len(name) > 4


@dataclass
class Def:
    path: Path
    qualname: str
    node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
    parent: ast.ClassDef | None

    @property
    def name(self) -> str:
        return self.node.name

    @property
    def kind(self) -> str:
        if isinstance(self.node, ast.ClassDef):
            return "class"
        if self.parent is None:
            return "function"
        decos = {deco_name(d) for d in self.node.decorator_list}
        if "property" in decos or "cached_property" in decos:
            return "property"
        return "method"

    @property
    def public(self) -> bool:
        return not any(is_private(p) or is_dunder(p) for p in self.qualname.split("."))

    @property
    def span(self) -> tuple[int, int]:
        return self.node.lineno, self.node.end_lineno or self.node.lineno

    def loc(self, base: Path | None = None) -> str:
        return f"{rel(self.path, base)}:{self.node.lineno}"


def deco_name(node: ast.expr) -> str:
    if isinstance(node, ast.Call):
        node = node.func
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def iter_defs(path: Path) -> Iterator[Def]:
    """Module-level functions and classes, and the methods of (nested) classes.

    Functions nested inside functions are not yielded: they are not addressable.
    """

    def walk(body: list[ast.stmt], prefix: str, parent: ast.ClassDef | None) -> Iterator[Def]:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield Def(path, prefix + node.name, node, parent)
            elif isinstance(node, ast.ClassDef):
                yield Def(path, prefix + node.name, node, parent)
                yield from walk(node.body, prefix + node.name + ".", node)

    yield from walk(parse(path).body, "", None)


def strip_docstring(body: list[ast.stmt]) -> list[ast.stmt]:
    if (
        body
        and isinstance(body[0], ast.Expr)
        and isinstance(body[0].value, ast.Constant)
        and isinstance(body[0].value.value, str)
    ):
        return body[1:]
    return body


class _Normalizer(ast.NodeTransformer):
    """Rename identifiers canonically; optionally erase constants and attribute names.

    ``constants=True`` makes tests that differ only in an argument value hash equal;
    ``accessors=True`` also erases attribute and called-function names, so tests that
    differ only in which accessor they call hash equal.
    """

    def __init__(self, constants: bool, accessors: bool, bound: set[str]) -> None:
        self.names: dict[str, str] = {}
        self.constants = constants
        self.accessors = accessors
        self.bound = bound

    def _canon(self, name: str) -> str:
        return self.names.setdefault(name, f"v{len(self.names)}")

    def visit_Name(self, node: ast.Name) -> ast.AST:
        # Free names (globals, builtins, imported helpers) say *what* is called and
        # are kept, unless accessors are being erased too.
        if node.id not in self.bound and not self.accessors:
            return node
        return ast.copy_location(ast.Name(id=self._canon(node.id), ctx=node.ctx), node)

    def visit_arg(self, node: ast.arg) -> ast.AST:
        node.arg = self._canon(node.arg)
        node.annotation = None
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if self.constants:
            return ast.copy_location(ast.Constant(value=type(node.value).__name__), node)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        self.generic_visit(node)
        if self.accessors:
            node.attr = "_a"
        return node

    def visit_keyword(self, node: ast.keyword) -> ast.AST:
        self.generic_visit(node)
        if self.accessors and node.arg:
            node.arg = "_k"
        return node


def bound_names(nodes: list[ast.AST]) -> set[str]:
    """Names bound inside ``nodes``: arguments, assignment/loop/with/except targets."""
    bound: set[str] = set()
    for n in nodes:
        for sub in ast.walk(n):
            if isinstance(sub, ast.arg):
                bound.add(sub.arg)
            elif isinstance(sub, ast.Name) and isinstance(sub.ctx, (ast.Store, ast.Del)):
                bound.add(sub.id)
            elif isinstance(sub, ast.ExceptHandler) and sub.name:
                bound.add(sub.name)
    return bound


def normalized_hash(
    nodes: list[ast.stmt] | ast.AST,
    *,
    constants: bool = False,
    accessors: bool = False,
    scope: ast.AST | None = None,
) -> str:
    """Hash ``nodes`` after normalisation; ``scope`` (the enclosing function) adds
    its arguments and locals to the names that are canonicalised."""
    dumped = normalized_dump(nodes, constants=constants, accessors=accessors, scope=scope)
    return hashlib.sha1(dumped.encode()).hexdigest()[:16]


def normalized_dump(
    nodes: list[ast.stmt] | ast.AST,
    *,
    constants: bool = False,
    accessors: bool = False,
    scope: ast.AST | None = None,
) -> str:
    """The normalised AST as text, for similarity rather than equality."""
    seq: list[ast.AST] = [nodes] if isinstance(nodes, ast.AST) else list(nodes)
    bound = bound_names(seq + ([scope] if scope is not None else []))
    norm = _Normalizer(constants, accessors, bound)
    return "\n".join(ast.dump(norm.visit(copy.deepcopy(n)), include_attributes=False) for n in seq)


def node_count(nodes: list[ast.stmt] | ast.AST) -> int:
    seq: list[ast.AST] = [nodes] if isinstance(nodes, ast.AST) else list(nodes)
    return sum(1 for n in seq for _ in ast.walk(n))


def parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    return p


def table(columns: list[str], rows: list[list[object]]) -> str:
    def cell(v: object) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")

    out = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    out += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return "\n".join(out)


def emit(args: argparse.Namespace, data: dict, markdown: str) -> None:
    if args.json:
        json.dump(data, sys.stdout, indent=2, default=str)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(markdown.rstrip() + "\n")
