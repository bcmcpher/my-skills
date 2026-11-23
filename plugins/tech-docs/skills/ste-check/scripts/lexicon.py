#!/usr/bin/env python3
"""Build a lexicon in the common format from a source dictionary.

Deterministic, stdlib only. The format is documented in references/lexicon-format.md.

    python3 -I lexicon.py build --from tsv words.tsv            # a hand-written word list
    python3 -I lexicon.py build --from tsv words.tsv -o out.json
    python3 -I lexicon.py build --from ste-pdf [<pdf>]           # ASD-STE100 Issue 9, local PDF
    python3 -I lexicon.py show <lexicon.json>                    # counts, to check a build

TSV input: one entry per line, `term<TAB>replacement[<TAB>pos]`. An empty replacement marks an
approved term. Separate more than one replacement with commas. `#` starts a comment line.

Output goes to ${XDG_DATA_HOME:-~/.local/share}/tech-docs/lexicons/<name>.json by default. The
builder refuses an output path inside a git work tree.
"""
import argparse
import json
import os
import re
import subprocess
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


# ── ASD-STE100 adapter ───────────────────────────────────────────────────────
# The dictionary is ASD's copyright. This code reads it from the user's own PDF at run time;
# nothing from the dictionary is stored in this file or in the repository.

STE_NAME = "ste100-issue9"
STE_DEFAULT_PDF = Path.home() / "Documents" / "ASD-STE100" / "ASD-STE100_ISSUE9.pdf"
# Entries on the dictionary pages (2-1-*), measured 2026-11-23. The introduction states 875 and
# 1274, but the pages hold 879 and 1317: two independent counts agree, and the 208 approved verbs
# match the PDF's own list of approved verbs. The check guards against parser drift.
STE_EXPECTED = {"approved": 879, "not_approved": 1317}

_POS_RE = "|".join(POS)
FOOTER = re.compile(r"Part 2 - Dictionary.*?Page (2-\d+-\S+)|Page (2-\d+-\S+)\s+Part 2 - Dictionary")
DICT_PAGE = re.compile(r"2-1-[A-Z]\d+$")
PAGE_FURNITURE = re.compile(r"^\s*(?:Word\s+Approved meaning|\(part of speech\)\s+ALTERNATIVES|"
                            r"\d{4}-\d{2}-\d{2}\s*$|ASD.STE100 Simplified Technical English)")
HEAD_PREFIX = re.compile(r"^(?:\S+ )+?\((?:" + _POS_RE + r")\),?")
POS_ONLY = re.compile(r"\((?:" + _POS_RE + r")\),?")
HEADWORD = re.compile(r"^(?P<word>.+?) \((?P<pos>" + _POS_RE + r")\)(?P<comma>,?)\s*$")
ALT = re.compile(r"^(?P<term>[A-Z0-9][A-Z0-9 '’./-]*?)\s*\((?P<pos>" + _POS_RE + r"|TN|TV)\)")
ALT_POS_ONLY = re.compile(r"^\((?P<pos>" + _POS_RE + r"|TN|TV)\)")
UPPER_START = re.compile(r"^[A-Z0-9][A-Z0-9 '’./-]*$")
COL_GAP = re.compile(r"\s{2,}")


def ste_text(pdf):
    try:
        out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True,
                             text=True, check=True)
    except FileNotFoundError as exc:
        raise LexiconError("pdftotext not found; install poppler-utils") from exc
    except subprocess.CalledProcessError as exc:
        raise LexiconError(f"pdftotext failed on {pdf}: {exc.stderr.strip()}") from exc
    return out.stdout


def ste_pages(text):
    """Yield (page id, lines) for the dictionary pages. Each footer closes its page."""
    buf = []
    for line in text.splitlines():
        m = FOOTER.search(line)
        if m:
            page = m.group(1) or m.group(2)
            if DICT_PAGE.match(page):
                yield page, buf
            buf = []
        else:
            buf.append(line)


def _split_forms(text):
    """COMES ON, CAME ON / (WORSE, WORST) / (also ARE, WERE) → lowercase forms."""
    text = re.sub(r"[()]", " ", text)
    text = re.sub(r"\balso\b", " ", text)
    return [" ".join(f.split()).lower() for f in text.split(",") if f.strip()]


def _clean_alt(term, approved_terms):
    """Cut example text that ran into column 2: keep the longest approved word prefix."""
    words = term.split()
    for n in range(len(words), 0, -1):
        candidate = " ".join(words[:n]).lower()
        if candidate in approved_terms:
            return candidate
    return term.lower()


def _join(segments):
    """Join column-1 lines; a line that ends in a hyphen continues the word (ELECTROMAG-NETIC)."""
    out = ""
    for s in segments:
        out = out[:-1] + s if out.endswith("-") else (f"{out} {s}" if out else s)
    return out


def _col1(line):
    """Split a line that starts in column 1. Return (column-1 text, column-2 start or None).

    Column 1 usually ends at a gap of two or more spaces. Where pdftotext closed the gap to one
    space, a part of speech ends the headword, or else the first word with a lowercase letter
    (column 2 of an approved word starts with a capitalized meaning) ends it.
    """
    m = HEAD_PREFIX.match(line)
    if m:
        end = m.end()
    else:
        gap = COL_GAP.search(line)
        end = gap.start() if gap else len(line.rstrip())
        if line[:1].isupper():
            depth = 0
            for tok in re.finditer(r"\S+", line[:end]):
                t = tok.group(0)
                if depth == 0 and tok.start() > 0 and not t.startswith("(") \
                        and any(c.islower() for c in t):
                    end = tok.start() - 1
                    break
                depth += t.count("(") - t.count(")")
    rest = line[end:]
    start = end + len(rest) - len(rest.lstrip()) if rest.strip() else None
    return line[:end].strip(), start


def ste_parse(text):
    """Return (entries, problems) from the pdftotext -layout output of the dictionary."""
    entries, problems = [], []
    head = []           # column-1 text of a headword still being read
    head_col2 = []      # column-2 text seen while the headword was still open
    cur = None          # the entry that column-2 lines belong to
    forms_open = False  # the last column-1 line ended with a comma
    alt_pending = None  # an alternative whose (pos) is on the next line
    c2 = 19

    def finish_head():
        nonlocal cur, forms_open, head, head_col2
        joined = _join(head)
        m = HEADWORD.match(joined)
        word, pos, comma = (m.group("word"), m.group("pos"), m.group("comma")) if m \
            else (joined.rstrip(","), None, "")
        forms = []
        paren = re.search(r"\s*\(([^)]*)\)", word)
        if paren:
            inner = paren.group(1).strip()
            outer = (word[:paren.start()] + word[paren.end():]).strip()
            if inner.startswith("or "):           # MATT (or MATTE)
                forms.append(inner[3:].strip().lower())
                word = outer
            elif inner == "prefix":               # re- (prefix)
                word = outer
            elif outer.lower() in inner.lower().split():  # case (in case of)
                word = inner
            else:                                 # provided (that), so (that)
                word = f"{outer} {inner}"
        word = word.strip()
        word = word.strip()
        letters = re.sub(r"[^A-Za-z]", "", word)
        approved = letters.isupper()
        if not approved and not letters.islower():
            problems.append(f"mixed-case headword: {word!r}")
        flush_alt()
        cur = make_entry(word.lower(), approved, pos=pos, forms=forms or None)
        cur["_alts"] = []
        entries.append(cur)
        forms_open = bool(comma)
        head, pending = [], head_col2
        head_col2 = []
        for t in pending:
            take_alt(t)

    def in_col2(start):
        return start is not None and abs(start - c2) <= 4

    def flush_alt():
        """Keep an alternative that has no part of speech: NOT DAMAGED."""
        nonlocal alt_pending
        if alt_pending is not None and cur is not None and not cur["approved"]:
            cur["_alts"].append((alt_pending, None))
        alt_pending = None

    def take_alt(text_):
        nonlocal alt_pending
        if head:
            head_col2.append(text_)
            return
        if cur is None or cur["approved"]:
            return
        seg = COL_GAP.split(text_.strip(), 1)[0]
        if alt_pending is not None:
            m = ALT_POS_ONLY.match(seg)
            if m:
                cur["_alts"].append((alt_pending, m.group("pos")))
                alt_pending = None
                return
            flush_alt()
        m = ALT.match(text_.strip())
        if m:
            cur["_alts"].append((m.group("term").strip(), m.group("pos")))
        elif UPPER_START.match(seg) and any(c.isalpha() for c in seg):
            alt_pending = seg

    def is_verb_form(seg):
        """PROTRUDES / PROTRUDED, or OCCURRED after OCCURS: verb forms without a comma."""
        word = seg.rstrip(",")
        return (cur is not None and cur["approved"] and cur.get("pos") == "v"
                and re.fullmatch(r"[A-Z]+", word) is not None
                and word[:3].lower() == cur["term"][:3]
                and word.endswith(("S", "D")))

    prev_col1 = False  # the previous text line started in column 1
    for _, lines in ste_pages(text):
        for line in lines:
            if "Approved meaning/" in line:
                c2 = line.index("Approved meaning/")
            if not line.strip() or PAGE_FURNITURE.match(line):
                continue
            if line[0].isspace():
                if head:  # a headword with no part of speech: FOR EXAMPLE
                    finish_head()
                start = len(line) - len(line.lstrip())
                if in_col2(start):
                    take_alt(line[start:])
                prev_col1 = False
                continue
            seg, start = _col1(line)
            is_pos_only = POS_ONLY.fullmatch(seg) is not None
            if head and not prev_col1:
                finish_head()
            if head:
                head.append(seg)
                if HEADWORD.match(_join(head)):
                    finish_head()
            elif cur is not None and (forms_open or (seg.startswith("(") and not is_pos_only)
                                      or (prev_col1 and is_verb_form(seg))):
                cur.setdefault("forms", []).extend(_split_forms(seg))
                forms_open = seg.endswith(",")
            else:
                flush_alt()
                head, head_col2 = [seg], []
                if HEADWORD.match(seg):
                    finish_head()
            if in_col2(start):
                take_alt(line[start:])
            prev_col1 = True
    if head:
        finish_head()
    flush_alt()

    approved_terms = {e["term"] for e in entries if e["approved"]}
    for e in entries:
        alts = e.pop("_alts")
        if e["approved"]:
            continue
        # No alternatives is legitimate: some entries give a sentence construction instead.
        out = []
        for term, pos in alts:
            a = {"term": _clean_alt(term, approved_terms) if pos not in KINDS else term.lower()}
            if pos in KINDS:
                a["kind"] = pos
                a["pos"] = "n" if pos == "TN" else "v"
            elif pos:
                a["pos"] = pos
            if a not in out:
                out.append(a)
        if out:
            e["alternatives"] = out
    return entries, problems


def from_ste_pdf(pdf):
    return ste_parse(ste_text(pdf))


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
        problems, expected = [], None
    else:
        pdf = Path(args.source or os.environ.get("STE100_PDF") or STE_DEFAULT_PDF).expanduser()
        if not pdf.is_file():
            raise LexiconError(f"STE PDF not found: {pdf} (pass a path or set STE100_PDF)")
        entries, problems = from_ste_pdf(pdf)
        lex = {"name": args.name or STE_NAME, "closed": True, "entries": entries}
        expected = STE_EXPECTED
    validate(lex, "built lexicon")
    c = counts(lex)
    for p in problems[:args.problems]:
        print(f"  problem: {p}", file=sys.stderr)
    if len(problems) > args.problems:
        print(f"  ... {len(problems) - args.problems} more problems", file=sys.stderr)
    if expected and (c["approved"], c["not_approved"]) != (expected["approved"],
                                                            expected["not_approved"]):
        raise LexiconError(
            f"counts differ from the verified Issue 9 counts: {c['approved']} approved "
            f"(expected {expected['approved']}), {c['not_approved']} not approved (expected "
            f"{expected['not_approved']}). Nothing written.")
    out = Path(args.output) if args.output else default_dir() / f"{lex['name']}.json"
    write(lex, out)
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
    b.add_argument("--from", dest="source_type", required=True, choices=["tsv", "ste-pdf"])
    b.add_argument("source", nargs="?",
                   help="the source file (ste-pdf default: $STE100_PDF, else "
                        "~/Documents/ASD-STE100/ASD-STE100_ISSUE9.pdf)")
    b.add_argument("--problems", type=int, default=20,
                   help="print up to N parse problems (default 20)")
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
