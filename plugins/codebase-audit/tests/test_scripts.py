"""Each sweep script finds the pattern planted for it in ``fixture/``.

Run from the repo root:

    uv run --python 3.12 --with pytest --with pytest-cov pytest plugins/codebase-audit/tests
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).parent
FIXTURE = HERE / "fixture"
SCRIPTS = HERE.parent / "skills" / "codebase-audit" / "scripts"


def run(script: str, *args: str) -> dict:
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args, "--json"],
        cwd=FIXTURE, capture_output=True, text=True, check=True,
    )
    return json.loads(out.stdout)


def test_inventory_outlines_a_module_by_line_range():
    data = run("inventory.py", "src/demo", "--outline-min", "10", "--class-min", "5")
    items = data["outlines"]["src/demo/core.py"]
    names = {i["name"]: (i["start"], i["end"]) for i in items}
    assert "load" in names and "Widget.size" in names
    assert names["load"][0] < names["load"][1]


def test_dup_logic_finds_the_renamed_copy_and_the_guard():
    data = run("dup_logic.py", "src/demo", "--min-nodes", "10")
    clusters = [{s["name"] for s in c} for c in data["functions"]]
    assert {"_clip", "_bound"} in clusters
    assert "networkx" in data["guards"]


def test_public_callers_reports_the_test_only_method():
    data = run("public_callers.py", "src/demo", "--tests", "tests")
    assert {r["name"] for r in data["test_only"]} == {"Widget.only_tests_call_this", "Widget.size"}
    unused = {r["name"]: r["exported"] for r in data["unused"]}
    assert unused == {"load": True, "Widget.dense_size": False}


def test_raise_taxonomy_flags_the_mixed_mode_refusals():
    data = run("raise_taxonomy.py", "src/demo")
    kinds = {s["kind"]: s["types"] for s in data["summary"]}
    assert kinds["unsupported mode"] == {"NotImplementedError": 1, "ValueError": 1}
    assert kinds["missing state"] == {"RuntimeError": 1}


def test_docstring_signature_finds_the_bad_value_and_the_phantom_param():
    data = run("docstring_signature.py", "src/demo")
    checks = {(i["param"], i["check"]) for i in data["issues"]}
    assert ("policy", "documented value not accepted") in checks
    assert ("extra", "documented, not in signature") in checks


def test_near_dupes_finds_the_argument_cluster_and_the_class_pair():
    data = run("test_near_dupes.py", "tests", "--min-nodes", "5")
    clusters = [{s["name"] for s in c} for c in data["argument"]]
    assert {"test_clip_low", "test_clip_high", "test_clip_none"} in clusters
    pairs = {(p["a"].split()[-1], p["b"].split()[-1]) for p in data["class_pairs"]}
    assert ("TestEdgeWidget", "TestNodeWidget") in pairs


def test_private_access_counts_the_private_import_and_attribute():
    data = run("test_private_access.py", "tests", "--src", "src/demo", "--package", "demo")
    uses = {u for s in data["sites"] for u in s["uses"]}
    assert "_clip" in uses and "._cache" in uses
    assert data["files"]["tests/test_core.py"]["imports"] == 1


def test_spec_inventory_pairs_the_sibling_requirements():
    data = run("spec_inventory.py", "specs", "--tests", "tests")
    pairs = [(d["a"][0], d["b"][0]) for d in data["duplicates"]]
    assert ("widget-edge", "widget-node") in pairs
    assert any("_cache" in line for _, _, line in data["implementation"])
    assert data["unmarked"] == []


def test_coverage_subsets_reads_a_context_database(tmp_path):
    pytest.importorskip("pytest_cov")
    work = tmp_path / "fixture"
    shutil.copytree(FIXTURE, work)
    (work / "conftest.py").write_text(
        "import sys, pytest\nsys.path.insert(0, 'src')\n"
        "def pytest_configure(config):\n    config.addinivalue_line('markers', 'spec(cap, req): requirement')\n"
    )
    subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--cov=demo", "--cov-branch",
         "--cov-context=test", "tests"],
        cwd=work, check=True, capture_output=True,
    )
    out = subprocess.run(
        [sys.executable, str(SCRIPTS / "coverage_subsets.py"), ".coverage", "--min-covered", "1", "--json"],
        cwd=work, capture_output=True, text=True, check=True,
    )
    pairs = json.loads(out.stdout)["pairs"]
    assert pairs, "the two size tests in one class share coverage"
