#!/usr/bin/env python3
"""Score the READMEs that the readme-* eval cases wrote, with the full STE checker.

Eval graders cannot run a script, so the STE score is computed here, after a run kept with
`--keep-temp`. Pass each kept run directory with a label:

    python3 -I score_readmes.py base-1=/tmp/.../run-1 plugin-1=/tmp/.../run-2 ...

For each README.md found under a directory (the first match, by path), it reports:
  score     the checker score with the STE lexicon and the run's .tech-terms
  words     words in the README prose
  leaks     jargon hits per 100 words
  coverage  the share of declared terms that the README uses, in the declared spelling
  variants  terms written two ways
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE.parent / "skills" / "ste-check" / "scripts" / "ste_check.py"
TERMS = HERE / "lib" / "boutiques.tech-terms"
sys.path.insert(0, str(CHECKER.parent))
import ste_check  # noqa: E402


def find_readme(root):
    hits = sorted(p for p in Path(root).rglob("README.md") if "boutiques" not in p.parts)
    return hits[0] if hits else None


def declared(path):
    return [t for t, _, _ in ste_check.read_terms_file(path, "t")]


def score(label, readme):
    r = subprocess.run([sys.executable, "-I", str(CHECKER), "--lexicon", "ste100-issue9",
                        "--terms", str(TERMS), "--root", str(readme.parent), "--json",
                        str(readme)], capture_output=True, text=True)
    if r.returncode:
        return {"label": label, "error": r.stderr.strip()}
    out = json.loads(r.stdout)
    text = ste_check.clean(readme.read_text(encoding="utf-8"))
    words = len(ste_check.WORD.findall(text))
    hits = sum(x["count"] for x in out["jargon"] or [])
    terms = declared(TERMS)
    used = [t for t in terms if re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", text)]
    return {"label": label, "score": out["files"][0]["score"], "words": words,
            "leaks_per_100": round(100 * hits / words, 1) if words else None,
            "coverage": f"{len(used)}/{len(terms)}", "variants": len(out["variants"]),
            "jargon": out["jargon"] is not None}


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    rows = []
    for arg in argv:
        label, _, path = arg.partition("=")
        readme = find_readme(path or label)
        rows.append(score(label, readme) if readme else {"label": label, "error": "no README.md"})
    cols = ["label", "score", "words", "leaks_per_100", "coverage", "variants", "jargon"]
    print("| " + " | ".join(cols) + " |")
    print("|" + "---|" * len(cols))
    for r in rows:
        print("| " + " | ".join(str(r.get(c, r.get("error", ""))) for c in cols) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
