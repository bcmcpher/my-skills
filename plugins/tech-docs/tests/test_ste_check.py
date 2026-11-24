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


# ── Regressions from the code review ─────────────────────────────────────────

def _lex(*entries, closed=True):
    return ste_check.Lexicons([ste_check.BUILTIN, {"name": "t", "closed": closed,
                                                   "entries": list(entries)}], [])


def _score(tmp_path, text, lex):
    doc = tmp_path / "a.md"
    doc.write_text(text, encoding="utf-8")
    ds = ste_check.DocSet(lex, set())
    return ds, ds.score_file(doc)


def _flags(res, rule):
    return [f for r in res["rows"] for f in r["flags"] if f.startswith(rule + ":")]


def test_a_suffix_strips_only_from_a_part_of_speech_it_inflects():
    lex = _lex({"term": "us", "approved": True, "pos": "pron"},
               {"term": "in", "approved": True, "pos": "prep"},
               {"term": "use", "approved": True, "pos": "v", "forms": ["used"]},
               {"term": "fast", "approved": True, "pos": "adj"},
               {"term": "be", "approved": True, "pos": "v", "forms": ["is"]},
               {"term": "the", "approved": True, "pos": "art"})
    look = lambda w: ste_check.Lexicons.lookup(w, lex.full)[0]  # noqa: E731
    assert look("user") == "unknown"     # not us + er, not use + r
    assert look("inner") == "unknown"    # in is a preposition
    assert look("thing") == "unknown"    # not the + ing
    assert look("faster") == "ok"        # -er inflects an adjective
    assert look("used") == "ok"
    assert look("being") == "form"       # a two-letter verb still inflects


def test_a_possessive_leak_is_listed_under_its_word(tmp_path):
    ds, _ = _score(tmp_path, "The grobber's tool is a grobber.\n", _lex())
    assert [x["word"] for x in ds.leak_list() if x["word"].startswith("grob")] == ["grobber"]


def test_a_phrase_with_punctuation_matches_its_term(tmp_path):
    lex = _lex({"term": "and/or", "approved": False, "alternatives": [{"term": "or"}]})
    ds, res = _score(tmp_path, "Use the tool and/or the help.\n", lex)
    assert _flags(res, "word") == ["word:and/or→or"]
    assert "and" not in {x["word"] for x in ds.leak_list()}


def test_a_multi_word_form_matches(tmp_path):
    lex = _lex({"term": "come on", "approved": True, "pos": "v", "forms": ["came on"]})
    ds, _ = _score(tmp_path, "The tool came on.\n", lex)
    assert {x["word"] for x in ds.leak_list()} & {"came", "on"} == set()


def test_a_missing_file_is_a_usage_error_and_a_bad_file_is_skipped(tmp_path):
    r = run("--root", str(tmp_path), str(tmp_path / "nope.md"))
    assert r.returncode == 2 and "nope.md" in r.stderr and "Traceback" not in r.stderr
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"Use the \xff tool.\n")
    good = tmp_path / "good.md"
    good.write_text("Use the tool.\n")
    r = run("--root", str(tmp_path), "--json", str(bad), str(good))
    assert r.returncode == 0 and "skipped" in r.stderr
    assert [f["file"] for f in json.loads(r.stdout)["files"]] == [str(good)]


def test_a_bigram_never_spans_inline_code(tmp_path):
    ds, _ = _score(tmp_path, "Run `y` time again.\n\nThe runtime is easy.\n", _lex())
    assert ds.variants() == []


def test_inline_code_with_a_suffix_is_not_a_leak(tmp_path):
    ds, _ = _score(tmp_path, "Use the `x`s and `a`-`b` here.\n", _lex())
    leaks = {x["word"] for x in ds.leak_list()}
    assert not leaks & {"codes", "code", "code-code"}


def test_the_noun_rule_reads_positions_and_only_real_determiners(tmp_path):
    lex = _lex({"term": "list", "approved": False, "pos": "v",
                "alternatives": [{"term": "show", "pos": "v"}]})
    _, res = _score(tmp_path, "Use the list and list it.\n", lex)
    assert _flags(res, "word") == ["word:list→show"]       # only the second list
    _, res = _score(tmp_path, "Read code list now.\n", lex)
    assert _flags(res, "word") == ["word:list→show"]       # prose code is not a determiner
    _, res = _score(tmp_path, "Read `x` list now.\n", lex)
    assert _flags(res, "word") == []                       # inline code is


def test_glossary_headings_count_only_in_a_heading_style_glossary():
    assert ste_check.glossary_terms("## Overview\n\n- **lexicon** — x.\n") == ["lexicon"]
    assert ste_check.glossary_terms("## lexicon\n\nA list.\n\n## leak\n\nA word.\n") == \
        ["lexicon", "leak"]


# ── Regressions from the second code review ──────────────────────────────────

def test_an_s_suffix_inflects_only_a_noun_or_verb_and_es_needs_a_sibilant():
    lex = _lex({"term": "new", "approved": True, "pos": "adj", "forms": ["newer", "newest"]},
               {"term": "us", "approved": True, "pos": "pron"},
               {"term": "use", "approved": True, "pos": "v", "forms": ["uses"]},
               {"term": "note", "approved": True, "pos": "n"},
               {"term": "box", "approved": True, "pos": "n"})
    look = lambda w: ste_check.Lexicons.lookup(w, lex.full)[:2]  # noqa: E731
    assert look("news") == ("unknown", "news")   # not new + s, so no false form flag
    assert look("notes") == ("ok", "note")       # not not + es
    assert look("boxes") == ("ok", "box")


def test_uses_counts_as_use_for_the_term_and_alternative_report(tmp_path):
    lex = _lex({"term": "us", "approved": True, "pos": "pron"},
               {"term": "use", "approved": True, "pos": "v"})
    ds, _ = _score(tmp_path, "Utilize the tool. The tool uses it.\n", lex)
    assert {(b["term"], b["alternative"]) for b in ds.both} == {("utilize", "use")}


def test_a_long_fence_holds_a_short_one(tmp_path):
    doc = "````markdown\n```bash\nfrobnicate now\n```\n````\nRead this.\n"
    _, res = _score(tmp_path, doc, _lex())
    assert [(r["sentence"], r["line"]) for r in res["rows"]] == [("Read this.", 6)]


def test_a_two_word_variant_needs_a_declared_spelling(tmp_path):
    ds, _ = _score(tmp_path, "Run the setup. Then set up the tool.\n", _lex(closed=False))
    assert ds.variants() == []
    lex = ste_check.Lexicons([ste_check.BUILTIN], [("setup", "TN", "t")])
    ds, _ = _score(tmp_path, "Run the setup. Then set up the tool.\n", lex)
    assert ds.variants() == [{"spellings": {"setup": 1, "set up": 1}, "declared": "setup"}]


def test_a_stray_backtick_never_eats_the_next_block():
    assert ste_check.clean("- Set `a\n- Then `b` runs.\n") == "- Set `a\n- Then CODE runs.\n"
    assert ste_check.clean("# Use `a\nNext para `b` here.\n") == \
        "# Use `a\nNext para CODE here.\n"


def test_a_bare_lexicon_name_ignores_a_local_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "ste100-issue9").mkdir()
    assert ste_check.resolve_lexicon("ste100-issue9") == \
        ste_check.lexmod.default_dir() / "ste100-issue9.json"
    assert ste_check.resolve_lexicon("./x.json") == Path("./x.json")


# ── Regressions from the third code review ───────────────────────────────────

def test_es_after_an_o_finds_its_base():
    lex = _lex({"term": "zero", "approved": True, "pos": "n"},
               {"term": "undo", "approved": False, "pos": "v",
                "alternatives": [{"term": "reverse", "pos": "v"}]})
    look = lambda w: ste_check.Lexicons.lookup(w, lex.full)[:2]  # noqa: E731
    assert look("zeroes") == ("ok", "zero")
    assert look("undoes") == ("word", "undo")


def test_an_unclosed_long_fence_is_not_closed_by_an_inner_short_one():
    doc = "Intro here.\n````md\n```sh\nx\n```\nStill code.\n"
    assert ste_check.clean(doc) == "Intro here.\n" + "\n" * 5   # runs to the end, as in CommonMark


def test_ignore_jargon_says_so_instead_of_reporting_zero_leaks(tmp_path):
    doc = tmp_path / "a.md"
    doc.write_text("Use the frobnicator.\n")
    base = ("--root", str(tmp_path), "--lexicon", str(CLOSED), "--ignore", "jargon")
    r = run(*base, str(doc))
    assert "jargon leaks" not in r.stdout and "jargon is ignored" in r.stdout
    assert "No declared terms" not in r.stdout
    out = json.loads(run(*base, "--json", str(doc)).stdout)
    assert out["jargon"] is None


def test_a_plural_two_word_variant_of_a_declared_term(tmp_path):
    lex = ste_check.Lexicons([ste_check.BUILTIN], [("dataset", "TN", "t")])
    ds, _ = _score(tmp_path, "Read the datasets. Then read the data sets.\n", lex)
    assert ds.variants() == [{"spellings": {"datasets": 1, "data sets": 1},
                              "declared": "dataset"}]
