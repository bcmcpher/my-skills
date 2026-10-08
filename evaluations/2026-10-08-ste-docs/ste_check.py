#!/usr/bin/env python3
"""Score Markdown docs against a subset of ASD-STE100 writing rules.

Heuristic, stdlib only. It checks the measurable STE rules — sentence length, passive voice,
-ing forms, a short list of non-approved words and hedges, more than one instruction per
sentence, paragraph length. It does not check the STE dictionary, which is ASD-licensed.

Score = percentage of sentences with no flags. The writing.md target is about 80%.

    python3 -I ste_check.py README.md docs/*.md
    python3 -I ste_check.py --show 10 README.md     # print the 10 worst sentences
    python3 -I ste_check.py --json README.md
    python3 -I ste_check.py --ignore ing README.md   # skip a rule
"""
import argparse
import json
import re
import sys

PROCEDURAL_MAX = 20
DESCRIPTIVE_MAX = 25
PARAGRAPH_MAX = 6

IMPERATIVES = set("""
add apply ask avoid build call change check choose clone commit configure confirm connect copy
create define delete describe disable do download edit enable ensure enter export find fix
follow give go import include install keep let list load make mark merge move name note open
pass pick point prefer press pull push put read record remove rename replace report restart
review run save see select send set show skip start state stop switch tell test try turn type
update upgrade use verify wait write
""".split())

# Not the STE dictionary: common words STE does not approve, with its usual replacement.
NON_APPROVED = {
    "utilize": "use", "utilise": "use", "leverage": "use", "facilitate": "help",
    "in order to": "to", "prior to": "before", "subsequently": "then", "commence": "start",
    "terminate": "stop", "approximately": "about", "additional": "more", "assist": "help",
    "obtain": "get", "sufficient": "enough", "numerous": "many", "via": "through",
    "whilst": "while", "in the event that": "if", "a number of": "some",
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
WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")


def clean(text):
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)          # front matter
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)                 # comments
    text = re.sub(r"^(```|~~~).*?^\1.*?$", "", text, flags=re.S | re.M)  # fences
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)                   # images
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)               # links -> text
    text = re.sub(r"`[^`]*`", "CODE", text)                            # inline code
    return text


def blocks(text):
    """Yield (kind, text) units: 'step' for numbered items, 'item', 'para'."""
    para = []
    for line in text.splitlines() + [""]:
        s = line.strip()
        starts_item = re.match(r"^([-*+]|\d+[.)])\s+", s)
        if not s or s.startswith(("#", "|", ">")) or re.match(r"^[-*_]{3,}$", s) or starts_item:
            if para:
                yield para[0], " ".join(para[1:])
                para = []
            if starts_item:
                kind = "step" if starts_item.group(1)[0].isdigit() else "item"
                para = [kind, s[starts_item.end():]]
            continue
        if para:
            para.append(s)
        else:
            para = ["para", s]


def sentences(text):
    protected = ABBREV.sub(lambda m: m.group(0).replace(".", "§"), text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(*_])", protected)
    return [p.replace("§", ".").strip() for p in parts if WORD.search(p)]


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
    bad = [w for w in NON_APPROVED if re.search(r"\b" + re.escape(w) + r"\b", low)]
    if bad:
        flags.append("word:" + ",".join(f"{w}→{NON_APPROVED[w]}" for w in bad))
    hedges = [h for h in HEDGES if re.search(r"\b" + h + r"\b", low)]
    if hedges:
        flags.append("hedge:" + ",".join(hedges))
    if procedural and re.search(
            r"(?:,|;|\band)\s+(?:then\s+)?(?:" + "|".join(sorted(IMPERATIVES)) + r")\b",
            sentence[len(words[0]) if words else 0:], re.I):
        flags.append("multi-instruction")
    return flags


def rule_of(flag):
    return flag.split(":")[0].split(" ")[0]


def score_file(path, ignore=()):
    text = clean(open(path, encoding="utf-8").read())
    rows, long_paras = [], 0
    for kind, body in blocks(text):
        sents = sentences(body)
        if kind == "para" and len(sents) > PARAGRAPH_MAX:
            long_paras += 1
        for s in sents:
            flags = [f for f in check(s, kind) if rule_of(f) not in ignore]
            rows.append({"sentence": s, "kind": kind, "flags": flags})
    n = len(rows)
    clean_n = sum(1 for r in rows if not r["flags"])
    by_rule = {}
    for r in rows:
        for f in r["flags"]:
            by_rule[rule_of(f)] = by_rule.get(rule_of(f), 0) + 1
    return {"file": path, "sentences": n,
            "score": round(100 * clean_n / n, 1) if n else None,
            "by_rule": dict(sorted(by_rule.items(), key=lambda kv: -kv[1])),
            "long_paragraphs": long_paras, "rows": rows}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--show", type=int, default=0, help="print the N most-flagged sentences")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--ignore", default="",
                    help="comma-separated rules to skip: length,passive,ing,word,hedge,multi-instruction")
    args = ap.parse_args()
    ignore = {r.strip() for r in args.ignore.split(",") if r.strip()}
    results = [score_file(f, ignore) for f in args.files]
    if args.json:
        for r in results:
            r.pop("rows")
        json.dump(results, sys.stdout, indent=2)
        print()
        return
    for r in results:
        rules = ", ".join(f"{k} {v}" for k, v in r["by_rule"].items()) or "none"
        print(f"{r['score']:>5}%  {r['sentences']:>4} sentences  {r['file']}")
        print(f"        flags: {rules}; paragraphs >{PARAGRAPH_MAX} sentences: {r['long_paragraphs']}")
        worst = sorted((x for x in r["rows"] if x["flags"]), key=lambda x: -len(x["flags"]))
        for x in worst[:args.show]:
            print(f"        - [{'; '.join(x['flags'])}] {x['sentence'][:160]}")


if __name__ == "__main__":
    main()
