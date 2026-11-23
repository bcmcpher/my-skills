"""ste_check.py finds every leak planted in fixtures/project, with synthetic lexicons only.

Run from the repo root:

    uv run --python 3.12 --with pytest pytest plugins/tech-docs/tests
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
PROJECT = FIXTURES / "project"
GUIDE = PROJECT / "docs" / "guide.md"
CLOSED = FIXTURES / "mini-closed.json"
SCRIPT = HERE.parent / "skills" / "ste-check" / "scripts" / "ste_check.py"
sys.path.insert(0, str(SCRIPT.parent))

import ste_check  # noqa: E402

PLANTED_LEAKS = {"frobnicator", "widgetry", "code", "graph", "code-graph"}


def run(*args: str, cwd: Path = HERE) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], cwd=cwd,
                          capture_output=True, text=True)


def run_json(*args: str) -> dict:
    r = run(*args, "--json")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_finds_every_planted_leak_with_the_declared_list():
    out = run_json("--root", str(PROJECT), "--lexicon", str(CLOSED), str(GUIDE))
    leaks = {x["word"]: x["count"] for x in out["jargon"]}
    assert set(leaks) == PLANTED_LEAKS
    assert leaks["frobnicator"] == 3
    first = {x["word"]: x["first"] for x in out["jargon"]}
    assert first["widgetry"].endswith("guide.md:8")


def test_without_the_declared_list_declared_terms_become_leaks(tmp_path):
    out = run_json("--root", str(tmp_path), "--lexicon", str(CLOSED), str(GUIDE))
    leaks = {x["word"] for x in out["jargon"]}
    assert leaks == PLANTED_LEAKS | {"codegraph", "grobber", "datastore"}
    assert out["declared"] == 0
    assert any("No declared terms" in n for n in out["notes"])


def test_word_form_and_variant_flags():
    out = run_json("--root", str(PROJECT), "--lexicon", str(CLOSED), str(GUIDE))
    f = out["files"][0]
    assert f["by_rule"]["word"] == 2       # utilize, assist (built-in lexicon)
    assert f["by_rule"]["form"] == 1       # Writing: not a listed form of write
    assert out["variants"] == [{"spellings": {"codegraph": 1, "code-graph": 1, "code graph": 1},
                                "declared": "codegraph"}]
    pairs = {(b["term"], b["alternative"]) for b in out["both"]}
    assert pairs == {("utilize", "use"), ("assist", "help")}


def test_suppression_counts_name_each_source():
    out = run_json("--root", str(PROJECT), "--lexicon", str(CLOSED), str(GUIDE))
    assert out["suppressed"] == {".tech-terms": 2, "GLOSSARY.md": 1}
    assert out["declared_used"] == {"codegraph": 1, "grobber": 1, "datastore": 1}


def test_jargon_is_off_without_a_closed_lexicon():
    out = run_json("--root", str(PROJECT), str(GUIDE))
    assert out["jargon"] is None
    assert "jargon" not in out["files"][0]["by_rule"]
    assert any("jargon is off" in n for n in out["notes"])


def test_jargon_does_not_lower_the_score(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("Use the frobnicator.\n")
    out = run_json("--root", str(tmp_path), "--lexicon", str(CLOSED), str(doc))
    assert out["files"][0]["by_rule"] == {"jargon": 1}
    assert out["files"][0]["score"] == 100.0


def test_jargon_mode_prints_only_the_leak_list():
    r = run("--root", str(PROJECT), "--lexicon", str(CLOSED), "--jargon", str(GUIDE))
    assert r.returncode == 0
    lines = r.stdout.splitlines()
    assert lines[0].split()[:2] == ["3", "frobnicator"]
    assert "sentences" not in r.stdout


def test_exits_zero_with_findings_and_two_on_a_bad_lexicon(tmp_path):
    assert run("--root", str(PROJECT), "--lexicon", str(CLOSED), str(GUIDE)).returncode == 0
    bad = tmp_path / "bad.json"
    bad.write_text('{"name": "x", "closed": true, "entries": [{"term": "a"}]}')
    r = run("--lexicon", str(bad), str(GUIDE))
    assert r.returncode == 2
    assert "'approved'" in r.stderr


def test_a_later_lexicon_overrides_an_earlier_one(tmp_path):
    override = tmp_path / "override.json"
    override.write_text(json.dumps({"name": "override", "closed": False, "entries": [
        {"term": "utilize", "approved": True}]}))
    out = run_json("--root", str(PROJECT), "--lexicon", str(CLOSED), "--lexicon", str(override),
                   str(GUIDE))
    assert out["files"][0]["by_rule"]["word"] == 1  # only assist is left


def test_terms_file_syntax(tmp_path):
    p = tmp_path / "terms"
    p.write_text("# comment\nC#\nfrobble\tTV\n\ngrobber  # note\n")
    assert ste_check.read_terms_file(p, "t") == [("C#", "TN", "t"), ("frobble", "TV", "t"),
                                                 ("grobber", "TN", "t")]


def test_glossary_and_key_terms_sources():
    text = ("# Doc\n\n## Key terms\n\n- **lexicon** — a word list.\n"
            "| Term | Meaning |\n|---|---|\n| leak | an undeclared word |\n\n## Next\n\n"
            "- **not a term** — outside the section.\n")
    section = ste_check.key_terms_section(text)
    assert ste_check.glossary_terms(section) == ["lexicon", "leak"]


def test_morphology():
    lex = ste_check.Lexicons([json.loads(CLOSED.read_text())], [("datastore", "TN", "t")])
    look = lambda w: ste_check.Lexicons.lookup(w, lex.full)[0]  # noqa: E731
    assert look("tools") == "ok"           # plural of an approved noun
    assert look("wrote") == "ok"           # a listed form
    assert look("writing") == "form"       # not a listed form
    assert look("commenced") == "word"     # inflection of a non-approved verb
    assert look("datastores") == "ok"      # plural of a declared term
    assert look("tool's") == "ok"          # possessive
    assert look("easy-use") == "ok"        # every part is known
    assert look("frobnicator") == "unknown"


def test_line_numbers_follow_each_sentence(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("```\ncode\n```\nFirst sentence here.\nSecond one is\nwrapped here.\n")
    res = ste_check.DocSet(ste_check.Lexicons([ste_check.BUILTIN], []), set()).score_file(doc)
    assert [r["line"] for r in res["rows"]] == [4, 5]


def test_indented_fences_and_non_ascii_words(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("1. Run this:\n\n   ```bash\n   python3 -I tool.py build\n   ```\n\n"
                   "Read about Diátaxis here.\n")
    res = ste_check.DocSet(ste_check.Lexicons([ste_check.BUILTIN], []), set()).score_file(doc)
    assert [r["sentence"] for r in res["rows"]] == ["Run this:", "Read about Diátaxis here."]
    assert ste_check.WORD.findall("Diátaxis") == ["Diátaxis"]
