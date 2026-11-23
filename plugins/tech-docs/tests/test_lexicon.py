"""lexicon.py builds the common format from a TSV list and refuses unsafe output paths.

Run from the repo root:

    uv run --python 3.12 --with pytest pytest plugins/tech-docs/tests
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"
SCRIPTS = HERE.parent / "skills" / "ste-check" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lexicon  # noqa: E402


def run(*args: str, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", str(SCRIPTS / "lexicon.py"), *args],
                          capture_output=True, text=True, env=env)


def test_tsv_build_writes_an_open_lexicon(tmp_path):
    out = tmp_path / "plain.json"
    r = run("build", "--from", "tsv", str(FIXTURES / "plain-words.tsv"), "-o", str(out))
    assert r.returncode == 0, r.stderr
    lex = json.loads(out.read_text())
    assert lex["name"] == "plain-words"
    assert lex["closed"] is False
    by_term = {e["term"]: e for e in lex["entries"]}
    assert by_term["utilize"] == {"term": "utilize", "approved": False, "pos": "v",
                                  "alternatives": [{"term": "use"}]}
    assert by_term["in order to"]["alternatives"] == [{"term": "to"}]
    assert [a["term"] for a in by_term["facilitate"]["alternatives"]] == ["help", "make easier"]
    assert by_term["use"]["approved"] is True
    assert "alternatives" not in by_term["use"]
    assert "5 entries (1 approved, 4 not approved)" in r.stdout


def test_default_output_goes_to_the_xdg_lexicon_dir(tmp_path):
    env = {"XDG_DATA_HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
    r = run("build", "--from", "tsv", str(FIXTURES / "plain-words.tsv"), "--name", "mine",
            env=env)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "tech-docs" / "lexicons" / "mine.json").is_file()


def test_build_refuses_a_path_inside_a_git_work_tree(tmp_path):
    (tmp_path / "repo" / ".git").mkdir(parents=True)
    out = tmp_path / "repo" / "sub" / "lex.json"
    r = run("build", "--from", "tsv", str(FIXTURES / "plain-words.tsv"), "-o", str(out))
    assert r.returncode == 2
    assert "inside the git work tree" in r.stderr
    assert not out.exists()


def test_show_prints_counts(tmp_path):
    out = tmp_path / "plain.json"
    run("build", "--from", "tsv", str(FIXTURES / "plain-words.tsv"), "-o", str(out))
    r = run("show", str(out))
    assert r.returncode == 0
    assert "5 entries, 5 terms, 1 approved, 4 not approved, closed=false" in r.stdout


def test_tsv_rejects_an_unknown_pos(tmp_path):
    src = tmp_path / "bad.tsv"
    src.write_text("utilize\tuse\tverb\n")
    r = run("build", "--from", "tsv", str(src), "-o", str(tmp_path / "x.json"))
    assert r.returncode == 2
    assert "pos 'verb'" in r.stderr


@pytest.mark.parametrize("lex, message", [
    ({"closed": False, "entries": []}, "'name'"),
    ({"name": "x", "closed": "no", "entries": []}, "'closed'"),
    ({"name": "x", "closed": False, "entries": [{"term": "a"}]}, "'approved'"),
    ({"name": "x", "closed": False,
      "entries": [{"term": "a", "approved": True, "alternatives": [{"term": "b"}]}]},
     "approved term cannot have"),
    ({"name": "x", "closed": False, "entries": [{"term": "a", "approved": True, "kind": "XN"}]},
     "TN or TV"),
])
def test_validate_rejects_malformed_lexicons(lex, message):
    with pytest.raises(lexicon.LexiconError, match=message):
        lexicon.validate(lex)
