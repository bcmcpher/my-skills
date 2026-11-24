#!/usr/bin/env python3
"""Score Markdown docs against ASD-STE100 writing rules and any loaded lexicons.

Heuristic, deterministic, stdlib only. A soft audit: it reports and always exits 0.

Sentence rules: length, passive voice, -ing forms, hedges, more than one instruction per
sentence, paragraph length. Lexicon rules: `word` (a term that is not approved), `form` (an
inflection that the lexicon does not list), `jargon` (a word in no loaded lexicon and not a
declared term; closed lexicons only), `variant` (one term written two ways in the doc set).

Score = percentage of sentences with no flags. `jargon` flags do not lower the score: concise
technical docs cannot avoid jargon, so the jargon report is a list to review. The writing.md
target is about 80%.

    python3 -I ste_check.py README.md docs/                       # built-in lexicon only
    python3 -I ste_check.py --lexicon ste100-issue9 README.md     # add a lexicon by name or path
    python3 -I ste_check.py --lexicon ste100-issue9 --jargon docs/ # print only the leak list
    python3 -I ste_check.py --terms terms.txt --show 10 README.md
    python3 -I ste_check.py --json README.md
    python3 -I ste_check.py --ignore ing README.md                # skip a rule

Declared technical terms come from `.tech-terms` at the project root (or `--terms <file>`) and
from the project glossary (GLOSSARY.md, docs/glossary.md, or a "Key terms" section).
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lexicon as lexmod  # noqa: E402

PROCEDURAL_MAX = 20
DESCRIPTIVE_MAX = 25
PARAGRAPH_MAX = 6
CODE = "CODE"  # what inline code becomes; counted as a word, never looked up

IMPERATIVES = set("""
add apply ask avoid build call change check choose clone commit configure confirm connect copy
create define delete describe disable do download edit enable ensure enter export find fix
follow give go import include install keep let list load make mark merge move name note open
pass pick point prefer press pull push put read record remove rename replace report restart
review run save see select send set show skip start state stop switch tell test try turn type
update upgrade use verify wait write
""".split())

# Not the STE dictionary: common words that STE does not approve, with a usual replacement.
BUILTIN = {
    "name": "builtin",
    "closed": False,
    "entries": [
        {"term": t, "approved": False, "alternatives": [{"term": a}]} for t, a in {
            "utilize": "use", "utilise": "use", "leverage": "use", "facilitate": "help",
            "in order to": "to", "prior to": "before", "subsequently": "then",
            "commence": "start", "terminate": "stop", "approximately": "about",
            "additional": "more", "assist": "help", "obtain": "get", "sufficient": "enough",
            "numerous": "many", "via": "through", "whilst": "while",
            "in the event that": "if", "a number of": "some",
        }.items()
    ],
}
HEDGES = ["perhaps", "possibly", "probably", "basically", "simply", "just", "really",
          "quite", "somewhat", "arguably", "fairly"]

ING_OK = set("""
thing things string strings nothing something anything everything during morning bring brings
ring spring ceiling king sibling siblings building buildings setting settings warning warnings
heading headings pending missing existing following
""".split())

PARTICIPLES_IRREGULAR = ("built|done|found|given|held|kept|known|left|made|put|read|run|seen|"
                         "sent|set|shown|taken|told|written|chosen|broken|driven|frozen|"
                         "hidden|spoken|stolen|thrown|withdrawn|bound|caught|brought|bought|"
                         "taught|thought|meant|lost|paid|said|sold|split|spent|struck|understood")
PASSIVE = re.compile(
    r"\b(?:is|are|was|were|be|been|being|gets|get|got)\s+(?:\w+ly\s+)?"
    r"(?:\w+ed|" + PARTICIPLES_IRREGULAR + r")\b", re.I)
ABBREV = re.compile(r"\b(e\.g|i\.e|etc|vs|cf|approx|Fig|No)\.", re.I)
WORD = re.compile(r"[^\W\d_](?:[\w'’-]*[^\W_])?")  # starts with a letter; Diátaxis is one word
IDENT = re.compile(r".*\d")  # ASD-STE100, v2: identifiers, never looked up



def skipped(token):
    """Inline code and identifiers: counted as words, never looked up."""
    return token == CODE or IDENT.match(token) is not None


# Inflection suffixes tried when a word is not itself a term: (suffix, restore, parts of
# speech the suffix inflects). None in the set is an entry with no part of speech. The -s
# suffixes inflect a noun or pronoun (plural) or a verb (third person), so news is not
# new + s. -s goes before -es, so uses is use + s, not us + es; -es needs a sibilant or an o
# before it (boxes, zeroes).
PLURAL = {"n", "v", "pron", None}  # ones, others, yours
VERB = {"v", None}
COMPARE = {"adj", "adv", None}
SIBILANT = re.compile(r"(?:s|x|z|ch|sh|o)$")  # and zeroes, undoes
SUFFIXES = [("ies", "y", PLURAL), ("s", "", PLURAL), ("es", "", PLURAL), ("ied", "y", VERB),
            ("ed", "", VERB), ("ed", "e", VERB), ("d", "", VERB), ("ing", "", VERB),
            ("ing", "e", VERB), ("er", "", COMPARE), ("er", "e", COMPARE),
            ("est", "", COMPARE), ("est", "e", COMPARE)]
MIN_BASE = 2  # being is be + ing. The part of speech, not length, stops user -> us + er

GLOSSARY_FILES = ("GLOSSARY.md", "docs/glossary.md")
MIN_VARIANT = 5                                 # letters in a two-word variant key
FUNCTION_POS = ("art", "prep", "conj", "pron")  # alternatives too common to pair


# ── Markdown to sentences ────────────────────────────────────────────────────

def _blank(m):
    return "\n" * m.group(0).count("\n")


def clean(text):
    """Strip what is not prose. Removed blocks keep their newlines, so line numbers hold."""
    text = re.sub(r"\A---\n.*?\n---\n", _blank, text, flags=re.S)        # front matter
    text = re.sub(r"<!--.*?-->", _blank, text, flags=re.S)               # comments
    # Fences, also indented. A fence closes on a bare run of its own character at least as
    # long, so a ```` block can hold a ``` block. The lookahead takes the whole opening run and
    # cannot give part of it back. As in CommonMark, a fence with no closer runs to the end.
    text = re.sub(r"^[ \t]*(?=((`|~)\2{2,}))\1.*?(?:^[ \t]*\1\2*[ \t]*$|\Z)", _blank, text,
                  flags=re.S | re.M)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                     # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)                 # links -> text
    # Inline code on one line. A span that wraps is scored as text: matching across lines
    # would pair a stray backtick with one in the next list item or heading.
    text = re.sub(r"`[^`\n]*`", _code, text)
    return text


def _code(m):
    """CODE, spaced off from an adjacent word character so `x`s cannot become CODEs."""
    s, e, t = m.start(), m.end(), m.string
    left = " " if s and re.match(r"[\w'’-]", t[s - 1]) else ""
    right = " " if e < len(t) and re.match(r"[\w'’-]", t[e]) else ""
    return left + CODE + right


def blocks(text):
    """Yield (kind, text, starts) units: 'step' for numbered items, 'item', 'para'.

    starts lists (offset in text, line number) for each source line of the unit.
    """
    kind, parts, starts = None, [], []

    def unit():
        return kind, " ".join(parts), starts

    for n, line in enumerate(text.splitlines() + [""], 1):
        s = line.strip()
        starts_item = re.match(r"^([-*+]|\d+[.)])\s+", s)
        if not s or s.startswith(("#", "|", ">")) or re.match(r"^[-*_]{3,}$", s) or starts_item:
            if kind:
                yield unit()
                kind = None
            if starts_item:
                kind = "step" if starts_item.group(1)[0].isdigit() else "item"
                parts, starts = [s[starts_item.end():]], [(0, n)]
            continue
        if kind:
            starts.append((len(" ".join(parts)) + 1, n))
            parts.append(s)
        else:
            kind, parts, starts = "para", [s], [(0, n)]


def line_of(body, sentence, starts, pos):
    """Return (line of sentence, offset after it) inside a unit's joined text."""
    at = body.find(sentence, pos)
    if at < 0:
        return starts[0][1], pos
    line = max((ln for off, ln in starts if off <= at), default=starts[0][1])
    return line, at + len(sentence)


def sentences(text):
    protected = ABBREV.sub(lambda m: m.group(0).replace(".", "§"), text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(*_])", protected)
    return [p.replace("§", ".").strip() for p in parts if WORD.search(p)]


# ── Lexicons ─────────────────────────────────────────────────────────────────

class Lexicons:
    """Stacked lexicons. A later lexicon overrides an earlier one for the same term."""

    def __init__(self, lexicons, declared):
        self.names = [(lx["name"], lx["closed"]) for lx in lexicons]
        self.closed = any(lx["closed"] for lx in lexicons)
        self.base = self._index(lexicons)
        self.declared = declared  # list of (term, kind, source)
        decl_lex = {"name": "declared", "closed": False, "entries": [
            {"term": t, "approved": True, "kind": k, "_source": src} for t, k, src in declared]}
        self.full = self._index(lexicons + [decl_lex]) if declared else self.base

    @staticmethod
    def _index(lexicons):
        terms, forms, phrases = {}, {}, {}
        for lx in lexicons:
            by_term = {}
            for e in lx["entries"]:
                term = e["term"].lower()
                if "..." in term:
                    continue
                by_term.setdefault(term, []).append(e)
            terms.update(by_term)  # override per term
        keys = set(terms)
        for term, entries in terms.items():
            for e in entries:
                if e["approved"]:
                    for f in e.get("forms", []):
                        forms.setdefault(f.lower(), term)
        for key in keys | set(forms):  # and/or keeps its slash; came on is a form of come on
            toks = tuple(w.lower() for w in WORD.findall(key))
            if len(toks) > 1:
                phrases.setdefault(toks[0], []).append((toks, key))
        for v in phrases.values():
            v.sort(key=lambda p: (-len(p[0]), p[1]))
        return {"terms": terms, "forms": forms, "phrases": phrases}

    @staticmethod
    def units(tokens, index):
        """Group tokens into lookup units (key, surface, start): the longest phrase first,
        else one word. CODE and identifiers split the run: no unit spans them."""
        out, i = [], 0
        low = [t.lower() for t in tokens]
        while i < len(tokens):
            if skipped(tokens[i]):
                i += 1
                continue
            for toks, key in index["phrases"].get(low[i], ()):
                n = len(toks)
                if tuple(low[i:i + n]) == toks and not any(map(skipped, tokens[i:i + n])):
                    surface = " ".join(tokens[i:i + n])
                    out.append((key, surface if surface.lower() == key else key, i))
                    i += n
                    break
            else:
                out.append((low[i], tokens[i], i))
                i += 1
        return out

    @classmethod
    def lookup(cls, word, index):
        """Return (status, term, entries): status is ok, word, form or unknown."""
        word = re.sub(r"['’]s$", "", word)
        status, term, entries = cls._lookup(word, index)
        if status == "unknown" and "-" in word:  # read-only: accept if every part is known
            parts = [cls._lookup(p, index) for p in word.split("-") if p]
            if parts and all(p[0] == "ok" for p in parts):
                return "ok", word, []
        return status, term, entries

    @staticmethod
    def permitted(term, entries):
        """Approved, or offered by its own entry as a technical noun or verb: list (v) → LIST (TN)."""
        return any(e["approved"] or any(a["term"].lower() == term and a.get("kind")
                                        for a in e.get("alternatives", []))
                   for e in entries)

    @classmethod
    def _lookup(cls, word, index):
        terms = index["terms"]
        if word in terms:
            entries = terms[word]
            if cls.permitted(word, entries):
                return "ok", word, entries
            return "word", word, entries
        if word in index["forms"]:
            return "ok", index["forms"][word], terms[index["forms"][word]]
        for suffix, restore, pos in SUFFIXES:
            if not word.endswith(suffix):
                continue
            base = word[:-len(suffix)] + restore
            if suffix == "es" and not SIBILANT.search(base):
                continue
            candidates = [base]
            if not restore and len(base) > MIN_BASE and base[-1] == base[-2]:
                candidates.append(base[:-1])  # stopped -> stop
            for b in candidates:
                if len(b) < MIN_BASE or b not in terms:
                    continue
                entries = [e for e in terms[b] if e.get("pos") in pos]
                if not entries:
                    continue  # inner: in is a preposition, so -er cannot inflect it
                approved = [e for e in entries if e["approved"]]
                if not approved:
                    return ("ok" if cls.permitted(b, entries) else "word"), b, entries
                if pos is PLURAL and any(e.get("pos") in (None, "n") for e in approved):
                    return "ok", b, entries
                if any(e.get("forms") for e in approved):
                    return "form", b, approved
                return "ok", b, entries
        return "unknown", word, []


def resolve_lexicon(arg):
    """A path if it looks like one (.json, a separator, ~); else a name in the lexicon dir."""
    if arg.endswith(".json") or "/" in arg or arg.startswith("~"):
        return Path(arg).expanduser()
    return lexmod.default_dir() / f"{arg}.json"


def read_terms_file(path, source):
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = re.sub(r"(^|\s)#.*$", "", line).rstrip()
        if not line.strip():
            continue
        parts = line.split("\t")
        term = parts[0].strip()
        kind = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "TN"
        if kind not in ("TN", "TV"):
            raise lexmod.LexiconError(f"{path}: kind {kind!r} for {term!r} must be TN or TV")
        out.append((term, kind, source))
    return out


def glossary_terms(text):
    """Defined terms in a glossary: bold item leads and first table cells. Headings count
    only in a glossary that has neither, one heading per term; else ## Overview would be a term."""
    items, heads = [], []
    for line in text.splitlines():
        s = line.strip()
        h = re.match(r"^#{2,6}\s+(.+?)\s*#*$", s)
        m = h or (re.match(r"^(?:[-*+]\s+)?\*\*([^*]+)\*\*", s)
                  or re.match(r"^\|\s*\**([^|*]+?)\**\s*\|", s))
        if not m:
            continue
        term = m.group(1).strip().rstrip(":").strip()
        if re.fullmatch(r"[-: ]+", term) or term.lower() in ("term", "terms", "key terms"):
            continue
        (heads if h else items).append(term)
    return items or heads


def key_terms_section(text):
    """The body of a "Key terms" section, up to the next heading of the same or higher level."""
    m = re.search(r"^(#{1,6})\s+Key terms\s*$", text, flags=re.M | re.I)
    if not m:
        return ""
    level = len(m.group(1))
    rest = text[m.end():]
    end = re.search(r"^#{1,%d}\s" % level, rest, flags=re.M)
    return rest[:end.start()] if end else rest


def declared_terms(root, terms_file, files):
    out = []
    tt = Path(terms_file) if terms_file else root / ".tech-terms"
    if tt.is_file():
        out += read_terms_file(tt, ".tech-terms" if not terms_file else str(terms_file))
    elif terms_file:
        raise lexmod.LexiconError(f"terms file not found: {terms_file}")
    for g in GLOSSARY_FILES:
        p = root / g
        if p.is_file():
            out += [(t, "TN", g) for t in glossary_terms(p.read_text(encoding="utf-8"))]
    for f in sorted(set(files) | {root / "README.md"}):
        try:
            text = Path(f).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue  # score_file reports it
        if text:
            section = key_terms_section(text)
            if section:
                out += [(t, "TN", f"Key terms ({Path(f).name})") for t in glossary_terms(section)]
    seen, unique = set(), []
    for t, k, src in out:
        if t.lower() not in seen:
            seen.add(t.lower())
            unique.append((t, k, src))
    return unique


# ── Checking ─────────────────────────────────────────────────────────────────

def check(sentence, kind):
    words = WORD.findall(sentence)
    first = words[0].lower() if words else ""
    procedural = kind == "step" or first in IMPERATIVES
    limit = PROCEDURAL_MAX if procedural else DESCRIPTIVE_MAX
    low = " " + sentence.lower() + " "
    flags = []
    if len(words) > limit:
        flags.append(f"length {len(words)}>{limit}")
    if PASSIVE.search(sentence):
        flags.append("passive")
    ing = [w for w in words if w.lower().endswith("ing") and len(w) > 4
           and w.lower() not in ING_OK and not w[0].isupper()]
    if ing:
        flags.append("ing:" + ",".join(ing[:3]))
    hedges = [h for h in HEDGES if re.search(r"\b" + h + r"\b", low)]
    if hedges:
        flags.append("hedge:" + ",".join(hedges))
    first_word = WORD.search(sentence)
    if procedural and first_word and re.search(
            r"(?:,|;|\band)\s+(?:then\s+)?(?:" + "|".join(sorted(IMPERATIVES)) + r")\b",
            sentence[first_word.end():], re.I):
        flags.append("multi-instruction")
    return flags


DETERMINERS = set("a an the this that these those each every its your our their my some no "
                  "all".split())


def noun_positions(tokens):
    """Indexes of words that follow a determiner or inline code, so are probably nouns."""
    return {i for i in range(1, len(tokens))
            if tokens[i - 1] == CODE or tokens[i - 1].lower() in DETERMINERS}


def alt_text(entries):
    alts = []
    for e in entries:
        for a in e.get("alternatives", []):
            if a["term"] not in alts:
                alts.append(a["term"])
    return "/".join(alts) or "?"


class DocSet:
    def __init__(self, lex, ignore):
        self.lex, self.ignore = lex, ignore
        self.leaks = {}          # word -> [count, first location]
        self.suppressed = Counter()
        self.lexical_hits = 0    # word + form + jargon hits, after declared terms
        self.spellings = {}      # variant key -> Counter of spellings
        self.single_keys = set()
        self.both = []           # (file, non-approved term, alternative, counts)
        self.declared_used = Counter()

    def lexical(self, sentence, where, file_terms):
        tokens = WORD.findall(sentence)
        after_det = noun_positions(tokens)
        flags = []
        bad_words, bad_forms, leaks = [], [], []
        for term, surface, at in self.lex.units(tokens, self.lex.full):
            status, base, entries = self.lex.lookup(term, self.lex.full)
            if status == "word" and at in after_det \
                    and not any(e.get("pos") == "n" for e in entries):
                status = "unknown"  # the file: a noun that STE lists only as a verb
            file_terms[base] += 1
            declared = [e for e in entries if "_source" in e]
            if status == "ok" and declared:
                self.declared_used[declared[0]["term"].lower()] += 1
                b_status, _, _ = self.lex.lookup(term, self.lex.base)
                if b_status in ("word", "form") or (b_status == "unknown" and self.lex.closed):
                    self.suppressed[declared[0]["_source"]] += 1
            if status == "word":
                bad_words.append(f"{surface}→{alt_text(entries)}")
            elif status == "form":
                listed = ",".join(f for e in entries for f in e.get("forms", []))
                bad_forms.append(f"{surface}({base}: {listed})")
            elif status == "unknown" and self.lex.closed and len(term) > 1 \
                    and "jargon" not in self.ignore:
                leaks.append(surface)
                key = re.sub(r"['’]s$", "", term)  # asd's leaks as asd
                rec = self.leaks.setdefault(key, [0, where])
                rec[0] += 1
        if bad_words and "word" not in self.ignore:
            flags.append("word:" + ",".join(bad_words))
            self.lexical_hits += len(bad_words)
        if bad_forms and "form" not in self.ignore:
            flags.append("form:" + ",".join(bad_forms))
            self.lexical_hits += len(bad_forms)
        if leaks and "jargon" not in self.ignore:
            flags.append("jargon:" + ",".join(leaks))
            self.lexical_hits += len(leaks)
        self._collect_spellings(tokens)
        return flags

    def _collect_spellings(self, tokens):
        """Count each spelling. A bigram never spans inline code or an identifier:
        run `y` time is not run time."""
        for t in tokens:
            if skipped(t):
                continue
            low = t.lower()
            key = re.sub(r"[-\s]", "", low)
            self.single_keys.add(key)
            self.spellings.setdefault(key, Counter())[low] += 1
        for a, b in zip(tokens, tokens[1:]):
            if skipped(a) or skipped(b):
                continue
            a, b = a.lower(), b.lower()
            key = a + b
            if len(key) >= MIN_VARIANT and "-" not in key:  # skip into / in to
                self.spellings.setdefault(key, Counter())[f"{a} {b}"] += 1

    def score_file(self, path):
        text = clean(Path(path).read_text(encoding="utf-8"))
        rows, long_paras = [], 0
        file_terms = Counter()
        for kind, body, starts in blocks(text):
            sents = sentences(body)
            if kind == "para" and len(sents) > PARAGRAPH_MAX:
                long_paras += 1
            pos = 0
            for s in sents:
                line, pos = line_of(body, s.replace("§", "."), starts, pos)
                flags = [f for f in check(s, kind) if rule_of(f) not in self.ignore]
                flags += self.lexical(s, f"{path}:{line}", file_terms)
                rows.append({"sentence": s, "kind": kind, "line": line, "flags": flags})
        self._both(path, file_terms)
        n = len(rows)
        scored = [r for r in rows if not [f for f in r["flags"] if rule_of(f) != "jargon"]]
        by_rule = Counter(rule_of(f) for r in rows for f in r["flags"])
        return {"file": str(path), "sentences": n,
                "score": round(100 * len(scored) / n, 1) if n else None,
                "by_rule": dict(sorted(by_rule.items(), key=lambda kv: -kv[1])),
                "long_paragraphs": long_paras, "rows": rows}

    def _both(self, path, file_terms):
        """A doc that uses a non-approved term and also its approved alternative."""
        if "variant" in self.ignore:
            return
        terms = self.lex.full["terms"]
        for term, n in file_terms.items():
            entries = terms.get(term, [])
            if not entries or self.lex.permitted(term, entries):
                continue
            alts = {a["term"].lower() for e in entries for a in e.get("alternatives", [])
                    if a.get("pos") not in FUNCTION_POS and len(a["term"]) > 2
                    and a["term"].lower() != term
                    and not any(x.get("pos") in FUNCTION_POS
                                for x in terms.get(a["term"].lower(), []))}
            for alt in sorted(alts):  # skip in order to / to: function words are everywhere
                if file_terms.get(alt):
                    self.both.append({"file": str(path), "term": term, "count": n,
                                      "alternative": alt, "alternative_count": file_terms[alt]})

    def variants(self):
        if "variant" in self.ignore:
            return []
        canon = {re.sub(r"[-\s]", "", t.lower()): t for t, _, _ in self.lex.declared}
        out = []
        for key, spellings in self.spellings.items():
            if key not in self.single_keys:
                continue
            singles = {s: c for s, c in spellings.items() if " " not in s}
            bigrams = {s: c for s, c in spellings.items() if " " in s}
            forms = dict(singles)
            declared = next((canon[k] for k in (key, re.sub(r"s$", "", key),  # data sets
                                                re.sub(r"es$", "", key)) if k in canon), None)
            if bigrams and singles and declared:  # setup / set up are both correct
                forms.update(bigrams)
            if len(forms) < 2:
                continue
            out.append({"spellings": dict(sorted(forms.items(), key=lambda kv: -kv[1])),
                        "declared": declared})
        out.sort(key=lambda v: -sum(v["spellings"].values()))
        return out

    def leak_list(self):
        """Leaks, most frequent first. A plural joins its singular when both leak: term(s)."""
        merged = {}
        for w, (c, where) in self.leaks.items():
            key = w[:-1] if w.endswith("s") and w[:-1] in self.leaks else w
            rec = merged.setdefault(key, [0, where, key])
            rec[0] += c
            if key != w:
                rec[2] = f"{key}(s)"
        return [{"word": label, "count": c, "first": where}
                for _, (c, where, label) in sorted(merged.items(),
                                                   key=lambda kv: (-kv[1][0], kv[0]))]


def rule_of(flag):
    return flag.split(":")[0].split(" ")[0]


def expand(paths):
    out = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            out += sorted(x for x in p.rglob("*.md") if ".git" not in x.parts)
        else:
            out.append(p)
    return out


def project_root(start):
    tree = lexmod.git_work_tree(start)
    return tree if tree else Path(start).resolve()


# ── Report ───────────────────────────────────────────────────────────────────

def notes(lex, ignore=()):
    out = []
    if "jargon" in ignore:
        out.append("jargon is ignored (--ignore jargon): leaks were not checked.")
    elif not lex.closed:
        out.append("jargon is off: no closed lexicon is loaded (try --lexicon ste100-issue9).")
    elif not lex.declared:
        out.append("No declared terms: every technical term shows as a leak. "
                   "Write a .tech-terms file from the code and manifests, not from these docs.")
    return out


def report(results, ds, lex, args, ignore):
    leaks = ds.leak_list()
    if args.jargon:
        for leak in leaks:
            print(f"{leak['count']:>5}  {leak['word']:<30} {leak['first']}")
        for n in notes(lex, ignore):
            print(f"note: {n}")
        return
    for r in results:
        rules = ", ".join(f"{k} {v}" for k, v in r["by_rule"].items()) or "none"
        score = f"{r['score']:>5}%" if r["score"] is not None else "  n/a "
        print(f"{score}  {r['sentences']:>4} sentences  {r['file']}")
        print(f"        flags: {rules}; paragraphs >{PARAGRAPH_MAX} sentences: "
              f"{r['long_paragraphs']}")
        worst = sorted((x for x in r["rows"] if x["flags"]), key=lambda x: -len(x["flags"]))
        for x in worst[:args.show]:
            print(f"        - L{x['line']} [{'; '.join(x['flags'])}] {x['sentence'][:160]}")
    names = ", ".join(f"{n} ({'closed' if c else 'open'})" for n, c in lex.names)
    by_src = Counter(src for _, _, src in lex.declared)
    decl = ", ".join(f"{s} {n}" for s, n in by_src.items()) or "none"
    print(f"\nlexicons: {names}; declared terms: {len(lex.declared)} ({decl})")
    if lex.closed and "jargon" not in ignore:
        hits = sum(leak["count"] for leak in leaks)
        print(f"jargon leaks: {len(leaks)} words, {hits} hits (not counted in the score)")
        for leak in leaks[:args.leaks]:
            print(f"  {leak['count']:>4}  {leak['word']:<28} {leak['first']}")
        if len(leaks) > args.leaks:
            print(f"  ... {len(leaks) - args.leaks} more (use --jargon for the full list)")
    variants = ds.variants()
    if variants or ds.both:
        print("variants:")
        for v in variants:
            spell = " / ".join(f"{s} ({c})" for s, c in v["spellings"].items())
            print(f"  {spell}" + (f" — declared: {v['declared']}" if v["declared"] else ""))
        for b in ds.both:
            print(f"  {b['term']} ({b['count']}) and its alternative {b['alternative']} "
                  f"({b['alternative_count']}) in {b['file']}")
    if lex.declared:
        total = ds.lexical_hits + sum(ds.suppressed.values())
        for src in by_src:
            n = ds.suppressed.get(src, 0)
            share = f"{100 * n / total:.0f}%" if total else "0%"
            print(f"declared terms from {src} suppressed {n} hits ({share} of all lexicon hits)")
    for n in notes(lex, ignore):
        print(f"note: {n}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Score Markdown docs against STE writing rules.")
    ap.add_argument("files", nargs="+", help="Markdown files or directories")
    ap.add_argument("--lexicon", action="append", default=[],
                    help="a lexicon name (in the lexicon directory) or a path (with .json, "
                         "/ or ~); repeat to stack (later overrides earlier)")
    ap.add_argument("--terms", help="declared terms file (default: .tech-terms at the root)")
    ap.add_argument("--root", help="project root for .tech-terms and the glossary "
                                   "(default: the git work tree, else the current directory)")
    ap.add_argument("--jargon", action="store_true", help="print only the jargon leak list")
    ap.add_argument("--show", type=int, default=0, help="print the N most-flagged sentences")
    ap.add_argument("--leaks", type=int, default=15, help="leaks to list in the report")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ignore", default="",
                    help="comma-separated rules to skip: length,passive,ing,word,form,hedge,"
                         "multi-instruction,jargon,variant")
    args = ap.parse_args(argv)
    ignore = {r.strip() for r in args.ignore.split(",") if r.strip()}
    files = expand(args.files)
    root = Path(args.root).resolve() if args.root else project_root(Path.cwd())
    try:
        lexicons = [lexmod.validate(BUILTIN, "builtin")]
        lexicons += [lexmod.load(resolve_lexicon(x)) for x in args.lexicon]
        declared = declared_terms(root, args.terms, files)
    except (lexmod.LexiconError, OSError) as exc:
        print(f"ste_check.py: {exc}", file=sys.stderr)
        return 2
    missing = [str(f) for f in files if not f.is_file()]
    if missing:
        print(f"ste_check.py: not a file or directory: {', '.join(missing)}", file=sys.stderr)
        return 2
    lex = Lexicons(lexicons, declared)
    ds = DocSet(lex, ignore)
    results = []
    for f in files:
        try:
            results.append(ds.score_file(f))
        except (OSError, UnicodeDecodeError) as exc:  # soft audit: skip it, check the rest
            print(f"ste_check.py: skipped {f}: {exc}", file=sys.stderr)
    if args.json:
        for r in results:
            r.pop("rows")
        json.dump({"files": results, "jargon": ds.leak_list()
                   if lex.closed and "jargon" not in ignore else None,
                   "variants": ds.variants(), "both": ds.both,
                   "lexicons": [{"name": n, "closed": c} for n, c in lex.names],
                   "declared": len(declared),
                   "declared_used": dict(ds.declared_used),
                   "suppressed": dict(ds.suppressed), "lexical_hits": ds.lexical_hits,
                   "notes": notes(lex, ignore)}, sys.stdout, indent=2)
        print()
        return 0
    report(results, ds, lex, args, ignore)
    return 0


if __name__ == "__main__":
    sys.exit(main())
