#!/usr/bin/env python3
"""Build a lexicon in the common format from a source dictionary.

Deterministic, stdlib only. The format is documented in references/lexicon-format.md.

    python3 -I lexicon.py build --from tsv words.tsv            # a hand-written word list
    python3 -I lexicon.py build --from tsv words.tsv -o out.json
    python3 -I lexicon.py show <lexicon.json>                    # counts, to check a build

TSV input: one entry per line, `term<TAB>replacement[<TAB>pos]`. An empty replacement marks an
approved term. Separate more than one replacement with commas. `#` starts a comment line.

Output goes to ${XDG_DATA_HOME:-~/.local/share}/tech-docs/lexicons/<name>.json by default. The
builder refuses an output path inside a git work tree.
"""
import argparse
import json
import os
import sys
from pathlib import Path

POS = ("n", "v", "adj", "adv", "pron", "art", "prep", "conj")
KINDS = ("TN", "TV")


class LexiconError(ValueError):
    pass


def default_dir():
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "tech-docs" / "lexicons"


def git_work_tree(path):
    """Return the work-tree root that contains path, or None."""
    p = Path(path).resolve()
    for d in [p, *p.parents]:
        if (d / ".git").exists():
            return d
    return None


def make_entry(term, approved, pos=None, kind=None, forms=None, alternatives=None):
    e = {"term": term, "approved": approved}
    if pos:
        e["pos"] = pos
    if kind:
        e["kind"] = kind
    if forms:
        e["forms"] = forms
    if alternatives:
        e["alternatives"] = alternatives
    return e


def validate(lex, source="lexicon"):
    """Raise LexiconError if lex is not a valid lexicon. Return lex."""
    def fail(msg):
        raise LexiconError(f"{source}: {msg}")

    if not isinstance(lex, dict):
        fail("top level must be an object")
    if not isinstance(lex.get("name"), str) or not lex["name"]:
        fail("'name' must be a non-empty string")
    if not isinstance(lex.get("closed"), bool):
        fail("'closed' must be true or false")
    if not isinstance(lex.get("entries"), list):
        fail("'entries' must be an array")
    for i, e in enumerate(lex["entries"]):
        where = f"entry {i}"
        if not isinstance(e, dict):
            fail(f"{where} must be an object")
        if not isinstance(e.get("term"), str) or not e["term"].strip():
            fail(f"{where}: 'term' must be a non-empty string")
        where = f"entry {i} ({e['term']!r})"
        if not isinstance(e.get("approved"), bool):
            fail(f"{where}: 'approved' must be true or false")
        if "pos" in e and e["pos"] not in POS:
            fail(f"{where}: 'pos' must be one of {', '.join(POS)}")
        if "kind" in e and e["kind"] not in KINDS:
            fail(f"{where}: 'kind' must be TN or TV")
        if "forms" in e and not (isinstance(e["forms"], list)
                                 and all(isinstance(f, str) and f for f in e["forms"])):
            fail(f"{where}: 'forms' must be an array of strings")
        alts = e.get("alternatives")
        if alts is not None:
            if e["approved"]:
                fail(f"{where}: an approved term cannot have 'alternatives'")
            if not isinstance(alts, list):
                fail(f"{where}: 'alternatives' must be an array")
            for a in alts:
                if not isinstance(a, dict) or not isinstance(a.get("term"), str) or not a["term"]:
                    fail(f"{where}: each alternative needs a 'term'")
                if "pos" in a and a["pos"] not in POS:
                    fail(f"{where}: alternative pos must be one of {', '.join(POS)}")
                if "kind" in a and a["kind"] not in KINDS:
                    fail(f"{where}: alternative kind must be TN or TV")
    return lex


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            lex = json.load(fh)
    except json.JSONDecodeError as exc:
        raise LexiconError(f"{path}: not valid JSON: {exc}") from exc
    return validate(lex, str(path))


def from_tsv(path):
    entries = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.split("\t")
            if len(fields) > 3:
                raise LexiconError(f"{path}:{n}: more than three tab-separated fields")
            term = fields[0].strip()
            repl = fields[1].strip() if len(fields) > 1 else ""
            pos = fields[2].strip() if len(fields) > 2 else ""
            if not term:
                raise LexiconError(f"{path}:{n}: empty term")
            if pos and pos not in POS:
                raise LexiconError(f"{path}:{n}: pos {pos!r} must be one of {', '.join(POS)}")
            alts = [{"term": a.strip()} for a in repl.split(",") if a.strip()]
            entries.append(make_entry(term, approved=not alts, pos=pos or None,
                                      alternatives=alts or None))
    return entries


def write(lex, out):
    out = Path(out)
    tree = git_work_tree(out.parent if not out.exists() else out)
    if tree:
        raise LexiconError(f"refusing to write {out}: it is inside the git work tree {tree}. "
                           "Lexicons derived from a dictionary stay out of repositories.")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(lex, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def counts(lex):
    terms = {}
    for e in lex["entries"]:
        terms.setdefault(e["term"].lower(), set()).add(e["approved"])
    return {
        "entries": len(lex["entries"]),
        "approved": sum(1 for e in lex["entries"] if e["approved"]),
        "not_approved": sum(1 for e in lex["entries"] if not e["approved"]),
        "terms": len(terms),
    }


def build(args):
    if args.source_type == "tsv":
        if not args.source:
            raise LexiconError("--from tsv needs a source file")
        name = args.name or Path(args.source).stem
        lex = {"name": name, "closed": False, "entries": from_tsv(args.source)}
    else:  # pragma: no cover - argparse restricts the choices
        raise LexiconError(f"unknown source type {args.source_type}")
    validate(lex, "built lexicon")
    out = Path(args.output) if args.output else default_dir() / f"{lex['name']}.json"
    write(lex, out)
    c = counts(lex)
    print(f"{out}: {c['entries']} entries ({c['approved']} approved, "
          f"{c['not_approved']} not approved), closed={str(lex['closed']).lower()}")
    return 0


def show(args):
    lex = load(args.lexicon)
    c = counts(lex)
    print(f"{lex['name']}: {c['entries']} entries, {c['terms']} terms, "
          f"{c['approved']} approved, {c['not_approved']} not approved, "
          f"closed={str(lex['closed']).lower()}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a lexicon in the common format.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="convert a source dictionary into a lexicon")
    b.add_argument("--from", dest="source_type", required=True, choices=["tsv"])
    b.add_argument("source", nargs="?", help="the source file")
    b.add_argument("--name", help="lexicon name (default: from the source)")
    b.add_argument("-o", "--output", help="output path (default: the lexicon directory)")
    s = sub.add_parser("show", help="print the counts of a lexicon")
    s.add_argument("lexicon")
    args = ap.parse_args(argv)
    try:
        return build(args) if args.cmd == "build" else show(args)
    except (LexiconError, OSError) as exc:
        print(f"lexicon.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
